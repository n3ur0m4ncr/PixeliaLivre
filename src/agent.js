'use strict';
// Project credit: n3urom4nc3r
// Pixelia Livre: modifications are restricted to the supported single-player game.
const GAME = Process.getModuleByName('GameAssembly.dll');
const MINIGAMES_SUPPORTED = __MINIGAMES_SUPPORTED__;
const BASKETBALL_SUPPORTED = __BASKETBALL_SUPPORTED__;
if (Process.arch !== 'ia32' || Process.mainModule.name.toLowerCase() !== 'to pixelia.exe')
  throw new Error('Esta edição exige To Pixelia para Windows, 32 bits.');
const NIL = ptr(0), PS = Process.pointerSize;
function api(name, ret, args) {
  return new NativeFunction(GAME.getExportByName('il2cpp_' + name), ret, args);
}
const A = {
  domain: api('domain_get','pointer',[]), attach: api('thread_attach','pointer',['pointer']),
  assemblies: api('domain_get_assemblies','pointer',['pointer','pointer']),
  image: api('assembly_get_image','pointer',['pointer']), imageName: api('image_get_name','pointer',['pointer']),
  klass: api('class_from_name','pointer',['pointer','pointer','pointer']),
  field: api('class_get_field_from_name','pointer',['pointer','pointer']),
  fieldType: api('field_get_type','pointer',['pointer']), typeName: api('type_get_name','pointer',['pointer']),
  flags: api('field_get_flags','int',['pointer']), offset: api('field_get_offset','int',['pointer']),
  staticGet: api('field_static_get_value','void',['pointer','pointer']),
  method: api('class_get_method_from_name','pointer',['pointer','pointer','int']),
  invoke: api('runtime_invoke','pointer',['pointer','pointer','pointer','pointer']),
  parent: api('class_get_parent','pointer',['pointer']),
  objectClass: api('object_get_class','pointer',['pointer'])
};
const domain = A.domain();
if (domain.isNull()) throw new Error('O jogo ainda está iniciando. Tente conectar novamente.');
A.attach(domain);
function str(s) { return Memory.allocUtf8String(s); }
const count=Memory.alloc(PS);count.writeU32(0);
const assemblies=A.assemblies(domain,count);
let image=NIL;
for (let i=0;i<count.readU32();i++) {
  const candidate=A.image(assemblies.add(i*PS).readPointer());
  if(A.imageName(candidate).readCString()==='Assembly-CSharp.dll')image=candidate;
}
if(image.isNull())throw new Error('Os componentes de To Pixelia ainda não foram carregados.');
function cls(n){
  let p=A.klass(image,str(''),str(n));
  if(p.isNull()&&n.startsWith('<')){
    const total=api('image_get_class_count','uint',['pointer'])(image);
    const at=api('image_get_class','pointer',['pointer','uint']);
    const name=api('class_get_name','pointer',['pointer']);
    for(let i=0;i<total;i++){const c=at(image,i);if(name(c).readCString()===n){if(!p.isNull())throw new Error('Classe ambígua: '+n);p=c;}}
  }
  if(p.isNull())throw new Error('Classe incompatível: '+n);return p;
}
const C={stats:cls('PlayerStats'),player:cls('Player'),time:cls('TimeManager'),scene:cls('SceneControllerManager'),ui:cls('UIManager'),statsUi:cls('StatsValueChange')};
function field(c,n,t,stat=false){
  const p=A.field(c,str(n));
  if(p.isNull() || A.typeName(A.fieldType(p)).readCString()!==t || Boolean(A.flags(p)&16)!==stat)
    throw new Error('Versão incompatível: campo '+n);
  return {p,offset:A.offset(p),type:t};
}
function method(c,n,argc){const p=A.method(c,str(n),argc);if(p.isNull()||p.readPointer().isNull())throw new Error('Método incompatível: '+n);return p;}
const skills=['computer','writing','cooking','guitar','piano','painting','drumming','singing','conversation','modelling','basketball','comedy','romance','lockpicking','driving','farming'];
const attributes=['intelligence'];
const needs=['hunger','energy','hygiene','toilet','mood','clothesHygiene'];
const F={};
for(const n of [...skills,...needs,'health'])F[n]=field(C.stats,n,'System.Single');
for(const n of attributes)F[n]=field(C.stats,n,'System.Int32');
F.money=field(C.stats,'money','System.Int32');
F.changed=field(C.stats,'statsChanged','System.Boolean');
const statsInstance=field(C.stats,'instance','PlayerStats',true);
const playerInstance=field(C.player,'instance','Player',true);
const sceneInstance=field(C.scene,'instance','SceneControllerManager',true);
const statsUiInstance=field(C.statsUi,'instance','StatsValueChange',true);
const blocked=field(C.scene,'sceneLoad_ActionBlocker','System.Boolean');
const paused=field(C.time,'gameClockPaused','System.Boolean');
const canWork=field(C.time,'gameClockCanWork','System.Boolean');
const clockFields={};for(const n of ['gameHour','gameMinute','gameSecond','gameDay'])clockFields[n]=field(C.time,n,'System.Int32');
const cachedPtr=A.field(C.stats,str('m_CachedPtr'));
if(cachedPtr.isNull())throw new Error('Unity Object incompatível.');
const cachedOffset=A.offset(cachedPtr);
const updatePlayer=method(C.player,'Update',0),updateTime=method(C.time,'Update',0);
const updateUi=method(C.ui,'Update',0),secondMethod=method(C.time,'UpdateGameSecond',2);
const updateMoney=method(C.ui,'ChangePlayerMoneyText',1);
const refreshStats=method(C.statsUi,'PauseMenuStatRefresh',0);
const secondNative=new NativeFunction(secondMethod.readPointer(),'void',['pointer','int','int','pointer']);
// Resolve the return address of the ordinary clock call; scripted skips are excluded.
const clockOrigins=new Set();
for(let p=updateTime.readPointer(),i=0;i<100;i++){
  const ins=Instruction.parse(p);
  if(ins.mnemonic==='call'&&ins.operands[0].type==='imm'&&ptr(ins.operands[0].value).equals(secondMethod.readPointer()))clockOrigins.add(ins.next.toString());
  if(ins.mnemonic==='ret'||ins.mnemonic==='int3')break;
  p=ins.next;
}
if(!clockOrigins.size)throw new Error('Não foi possível validar o controle do relógio nesta versão.');
const temp=Memory.alloc(PS);
function instance(f){A.staticGet(f.p,temp);return temp.readPointer();}
function alive(p,c){return !p.isNull() && !p.add(cachedOffset).readPointer().isNull() && (!c||A.objectClass(p).equals(c));}
function current(){
  const s=instance(statsInstance),p=instance(playerInstance),sc=instance(sceneInstance);
  if(!alive(s,C.stats)||!alive(p,C.player)||!alive(sc,C.scene)||sc.add(blocked.offset).readU8())return NIL;
  return s;
}
function get(p,f){const a=p.add(f.offset);return f.type==='System.Single'?a.readFloat():f.type==='System.Boolean'?Boolean(a.readU8()):a.readS32();}
function put(p,f,v){const a=p.add(f.offset);if(f.type==='System.Single')a.writeFloat(v);else if(f.type==='System.Boolean')a.writeU8(v?1:0);else a.writeS32(v);}
function invoke(m,obj,values=[]){
  const args=values.length?Memory.alloc(values.length*PS):NIL;
  const storage=values.map(v=>{const b=Memory.alloc(4);b.writeS32(v);return b;});
  storage.forEach((v,i)=>args.add(i*PS).writePointer(v));
  const error=Memory.alloc(PS);error.writePointer(NIL);
  const result=A.invoke(m,obj,args,error);
  if(!error.readPointer().isNull())throw new Error('O jogo recusou a atualização da interface.');
  return result;
}
function defaults(){return {freezeNeeds:false,freezeHealth:false,speed:1,autoMinigames:false,autoBasket:false};}
let options=defaults();
let latest={connected:true,ready:false,status:'Conectado. Entre em uma partida para habilitar o painel.',skills:{},...options};
let lastFrame=0,lastSnapshot=0,lastFault='',ui=NIL,time=NIL,boosting=false,closed=false;
let tasks=[];
let lease=Date.now();
function fault(e){
  options=defaults();
  latest.ready=false; latest.status='Mod pausado: '+e.message;
  if(lastFault!==latest.status){lastFault=latest.status;send({kind:'error',message:latest.status});}
}
function enforce(s){
  if(options.freezeNeeds)for(const n of needs)put(s,F[n],100);
  if(options.freezeHealth)put(s,F.health,100);
}
function refresh(s,withSkills=false){
  put(s,F.changed,true);
  // The value has already been committed. A cosmetic error must not invite a duplicate retry.
  try{
    if(alive(ui,C.ui))invoke(updateMoney,ui,[get(s,F.money)]);
    const target=instance(statsUiInstance);
    if(withSkills&&alive(target,C.statsUi))invoke(refreshStats,target);
  }catch(e){send({kind:'warning',message:'Valor aplicado; reabra a tela de atributos para atualizar a interface.'});}
}
function readSnapshot(s){
  const sk={};for(const n of skills)sk[n]=get(s,F[n]);
  const at={};for(const n of attributes)at[n]=get(s,F[n]);
  const ns={};for(const n of [...needs,'health'])ns[n]=get(s,F[n]);
  const clock={};if(alive(time,C.time))for(const n in clockFields)clock[n]=get(time,clockFields[n]);
  return {connected:true,ready:true,status:'Conectado ao To Pixelia. Opções prontas.',money:get(s,F.money),skills:sk,attributes:at,needs:ns,clock,...options};
}
function validate(name,value){
  if(['needs','health','minigames','basket'].includes(name)){if(typeof value!=='boolean')throw new Error('Opção inválida.');if(value&&name==='minigames'&&!MINIGAMES_SUPPORTED)throw new Error('Assistência de minigames indisponível nesta versão do jogo.');if(value&&name==='basket'&&!BASKETBALL_SUPPORTED)throw new Error('Assistência de basquete indisponível nesta versão do jogo.');}
  else if(name==='speed'){if(![1,2,5,10,20].includes(value))throw new Error('Velocidade inválida.');}
  else if(name==='addmoney'){if(!Number.isInteger(value)||value<1||value>10000000)throw new Error('Informe de 1 a 10.000.000.');}
  else if(name==='skill'){if(!value||!skills.includes(value.name)||!Number.isInteger(value.value)||value.value<0||value.value>100)throw new Error('Habilidade ou nível inválido.');}
  else if(name==='allskills'){if(!Number.isInteger(value)||value<0||value>100)throw new Error('Informe um nível de 0 a 100.');}
  else if(name==='attribute'){if(!value||!attributes.includes(value.name)||!Number.isInteger(value.value)||value.value<0||value.value>100)throw new Error('Atributo ou nível inválido.');}
  else if(name!=='refill')throw new Error('Comando desconhecido.');
}
function execute(name,value,s){
  if(name==='needs')options.freezeNeeds=value;
  else if(name==='health')options.freezeHealth=value;
  else if(name==='minigames')options.autoMinigames=value;
  else if(name==='basket')options.autoBasket=value;
  else if(name==='speed')options.speed=value;
  else if(name==='addmoney'){
    const old=get(s,F.money);
    if(old<0||old>2000000000||old+value>2000000000)throw new Error('Limite de dinheiro atingido (2 bilhões).');
    put(s,F.money,old+value);refresh(s);
  } else if(name==='skill'){put(s,F[value.name],value.value);refresh(s,true);}
  else if(name==='allskills'){for(const n of skills)put(s,F[n],value);refresh(s,true);}
  else if(name==='attribute'){put(s,F[value.name],value.value);refresh(s,true);}
  else if(name==='refill'){for(const n of needs)put(s,F[n],100);put(s,F.changed,true);}
  enforce(s);latest=readSnapshot(s);return latest;
}

let keysApi=null;const heldKeys=new Set();
try{
  const u=Process.getModuleByName('user32.dll');
  keysApi={key:new NativeFunction(u.getExportByName('GetAsyncKeyState'),'int16',['int'],'stdcall'),window:new NativeFunction(u.getExportByName('GetForegroundWindow'),'pointer',[],'stdcall'),pid:new NativeFunction(u.getExportByName('GetWindowThreadProcessId'),'uint',['pointer','pointer'],'stdcall')};
}catch(e){send({kind:'warning',message:'Atalhos indisponíveis; utilize o painel.'});}
function hotkeys(s){
  if(!keysApi)return;
  const owner=Memory.alloc(4);owner.writeU32(0);keysApi.pid(keysApi.window(),owner);
  const active=owner.readU32()===Process.id && (keysApi.key(0x11)&0x8000) && (keysApi.key(0x12)&0x8000);
  for(const code of [0x75,0x76,0x77,0x78,0x79,0x7a,0x7b]){
    const down=active && (keysApi.key(code)&0x8000);
    if(down&&!heldKeys.has(code)){
      heldKeys.add(code);lease=Date.now();
      try{
        if(code===0x75)execute('needs',!options.freezeNeeds,s);
        if(code===0x76)execute('addmoney',10000,s);
        if(code===0x77)execute('allskills',100,s);
        if(code===0x78){const speeds=[1,2,5,10,20];execute('speed',speeds[(speeds.indexOf(options.speed)+1)%speeds.length],s);}
        if(code===0x79)execute('health',!options.freezeHealth,s);
        if(MINIGAMES_SUPPORTED&&code===0x7a)execute('minigames',!options.autoMinigames,s);
        if(BASKETBALL_SUPPORTED&&code===0x7b)execute('basket',!options.autoBasket,s);
      }catch(e){send({kind:'error',message:e.message});}
    }else if(!down)heldKeys.delete(code);
  }
}

function frame(){
  if(closed)return;
  try{
    if(Date.now()-lease>5000)options=defaults();
    lastFrame=Date.now();const s=current();
    if(s.isNull()){
      latest={connected:true,ready:false,status:'Aguardando uma partida carregada.',skills:{},...options};
      for(const t of tasks.splice(0)){clearTimeout(t.timer);t.reject(new Error('Aguarde o carregamento da partida.'));}
      return;
    }
    hotkeys(s);enforce(s);
    if(typeof minigameMaintenance==='function')minigameMaintenance();
    for(const t of tasks.splice(0)){
      clearTimeout(t.timer);try{t.resolve(execute(t.name,t.value,s));}catch(e){t.reject(e);}
    }
    if(Date.now()-lastSnapshot>250){latest=readSnapshot(s);lastSnapshot=Date.now();}
  }catch(e){fault(e);}
}
const hooks=[];
hooks.push(Interceptor.attach(updatePlayer.readPointer(),{onEnter(){frame();},onLeave(){if(!closed)try{const s=current();if(!s.isNull())enforce(s);}catch(e){fault(e);}}}));
hooks.push(Interceptor.attach(updateTime.readPointer(),{onEnter(args){time=args[0];frame();}}));
hooks.push(Interceptor.attach(updateUi.readPointer(),{onEnter(args){ui=args[0];}}));
hooks.push(Interceptor.attach(secondMethod.readPointer(),{
  onEnter(args){
    this.extra=0;
    if(closed||boosting)return;
    try{
      const s=current();if(s.isNull())return;
      enforce(s);this.tm=args[0];this.mi=args[3];
      // Only multiply ordinary one-second clock ticks. Never multiply scripted time jumps.
      if(clockOrigins.has(this.returnAddress.toString())&&args[1].toInt32()===1&&args[2].toInt32()!==0&&!get(this.tm,paused)&&get(this.tm,canWork))this.extra=options.speed-1;
    }catch(e){fault(e);}
  },
  onLeave(){
    if(closed||boosting)return;
    try{
      boosting=true;
      for(let i=0;i<this.extra;i++){
        const s=current();if(s.isNull()||get(this.tm,paused)||!get(this.tm,canWork))break;
        enforce(s);secondNative(this.tm,1,1,this.mi);
      }
      const s=current();if(!s.isNull())enforce(s);
    }catch(e){fault(e);}finally{boosting=false;}
  }
}));
rpc.exports={
  snapshot(){
    lease=Date.now();
    if(lastFrame&&Date.now()-lastFrame>2500)return {...latest,ready:false,status:'O jogo está carregando ou sem atualizar. Aguarde.',...options};
    return {...latest,...options};
  },
  command(name,value){
    lease=Date.now();
    validate(name,value);
    if(closed||!latest.ready||Date.now()-lastFrame>2500)throw new Error('Entre em uma partida e aguarde o carregamento.');
    if(tasks.length>=10)throw new Error('Aguarde o comando anterior.');
    return new Promise((resolve,reject)=>{
      const t={name,value,resolve,reject};
      t.timer=setTimeout(()=>{tasks=tasks.filter(x=>x!==t);reject(new Error('O jogo não respondeu. O comando foi cancelado.'));},2000);
      tasks.push(t);
    });
  },
  shutdown(){
    closed=true;options=defaults();
    for(const t of tasks.splice(0)){clearTimeout(t.timer);t.reject(new Error('Mod desconectado.'));}
    for(const h of hooks)h.detach();
    return true;
  }
};
