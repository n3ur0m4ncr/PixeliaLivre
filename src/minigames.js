// Legacy hook definitions; these are not loaded by the current game-build manifest.
// Project credit: n3urom4nc3r
// Legacy hooks for Steam build 23486352. Do not load on newer builds without RVA revalidation.
// Note: Basketball shot hooks were revalidated for v1.1.28 and moved to basketball.js.
function miniEnabled(basket=false){
  return !closed && Date.now()-lease<=5000 && (basket?options.autoBasket:options.autoMinigames);
}
function miniProbe(cn,mn,rva,mnemonic,operands,change,basket=false){
  const start=method(cls(cn),mn,0).readPointer();
  const at=GAME.base.add(rva),distance=at.sub(start).toInt32();
  const ins=Instruction.parse(at);
  if(distance<0||distance>0x3000||ins.mnemonic!==mnemonic||ins.opStr!==operands)
    throw new Error('Verificação do minigame falhou: '+cn+'.'+mn);
  hooks.push(Interceptor.attach(at,function(){
    if(!miniEnabled(basket))return;
    try{change(this.context);}catch(e){fault(e);}
  }));
}

function miniHook(cn,mn,argc,enter,leave){
  const c=cls(cn),m=method(c,mn,argc);
  // Shared empty stubs are not activity-specific and must never be hooked.
  if(m.readPointer().equals(GAME.base.add(0x20c590)))throw new Error('Minigame sem implementação: '+cn+'.'+mn);
  hooks.push(Interceptor.attach(m.readPointer(),{
    onEnter(args){
      this.miniActive=miniEnabled();this.object=args[0];
      if(this.miniActive)try{enter?.(args,this);}catch(e){this.miniActive=false;fault(e);}
    },
    onLeave(ret){if(this.miniActive&&miniEnabled())try{leave?.(ret,this);}catch(e){fault(e);}}
  }));
}
miniHook('MG_GuitarManager','CHECK_NoteSuccess',1,args=>{args[1]=ptr(1);});
miniHook('DisabledMinigameManager','SIMULATED_ACTITIVTY_IsItSuccessfulActivity',1,null,ret=>ret.replace(1));

// Match the requested pose at the existing hit event, preserving timing and rewards.
// The two collision methods each take one collider argument.
function hitProbe(cn,rva,mnemonic,operands,change,event='OnTriggerEnter2D'){
  const start=method(cls(cn),event,1).readPointer();
  const at=GAME.base.add(rva),ins=Instruction.parse(at);
  if(at.sub(start).toInt32()<0||at.sub(start).toInt32()>0x1000||ins.mnemonic!==mnemonic||ins.opStr!==operands)
    throw new Error('Evento de acerto incompatível: '+cn);
  hooks.push(Interceptor.attach(at,function(){if(miniEnabled())try{change(this.context);}catch(e){fault(e);}}));
}
hitProbe('ModelPoses',0x581ccb,'cmp','ebx, eax',c=>{c.ebx=c.eax;});
hitProbe('DancingPose',0xd13b99,'cmp','edi, eax',c=>{c.edi=c.eax;});
hitProbe('RunnerPlayer',0x384942,'test','al, al',c=>{c.eax=ptr(0);});
for(const rva of [0x64c995,0x64c9bd])hitProbe('WormPlayer',rva,'test','al, al',c=>{c.eax=ptr(0);});
miniProbe('<SelectedLetter>d__25','MoveNext',0x4e33d4,'test','al, al',c=>{c.eax=ptr(1);});
miniProbe('<WaiterOrderCorrectFalseCheck>d__13','MoveNext',0x6023ba,'cmp','esi, dword ptr [ecx + 0x14]',c=>{c.esi=ptr(c.ecx.add(20).readS32());});

// Align only the temporary coordinates used by the timing check.
miniProbe('ReadingPressArrow','PressKeyToStop',0x730314,'movss','xmm1, dword ptr [ebp - 4]',c=>c.ebp.sub(4).writeFloat(c.eax.readFloat()));
miniProbe('ButcherPressArrow','PressKeyToStop',0x57464a,'movss','xmm1, dword ptr [ebp - 4]',c=>c.ebp.sub(4).writeFloat(c.eax.readFloat()));
for(const rva of [0x3a5c6f,0x3a6150])
  miniProbe('PuzzlePiece','RotateCorrectionCheck',rva,'cmp','edi, dword ptr [eax + 0xc]',c=>{c.edi=ptr(c.eax.add(12).readS32());});
for(const rva of [0x3a5cb4,0x3a6195])
  miniProbe('PuzzlePiece','RotateCorrectionCheck',rva,'movss','xmm0, dword ptr [eax + 8]',c=>c.eax.add(8).writeFloat(0));
// Arithmetic puzzles: use the expected result after native input/slot validation.
miniProbe('DigitCode','Select_UnSelect_DigitCode',0x5967fa,'movss','xmm0, dword ptr [ebp - 8]',c=>c.ebp.sub(8).writeFloat(c.ebp.add(8).readFloat()));
miniProbe('DigitCode','Select_UnSelect_DigitCode',0x597054,'movss','xmm0, dword ptr [ebp - 4]',c=>c.ebp.sub(4).writeFloat(c.ebp.sub(12).readFloat()));

const miniCache=new Map();
function miniClass(name,fields){
  if(miniCache.has(name))return miniCache.get(name);
  const c=cls(name),result={c,fields:{}};
  for(const [name,type] of Object.entries(fields))result.fields[name]=field(c,name,type);
  const instanceField=A.field(c,str('instance'));
  if(!instanceField.isNull()&&(A.flags(instanceField)&16))result.instance=field(c,'instance',name,true);
  miniCache.set(name,result);return result;
}
function miniObject(info){const p=info.instance?instance(info.instance):NIL;return alive(p,info.c)?p:NIL;}
const writing=miniClass('MG_WritingManager',{constructedWord:'System.String'});
const fieldSet=api('field_set_value','void',['pointer','pointer','pointer']);
miniProbe('LetterWMG','SelectedLetter',0x78c0bf,'push','0',c=>{
  const p=miniObject(writing);if(p.isNull()||c.esi.isNull())return;
  const value=Memory.alloc(PS);value.writePointer(c.esi);
  fieldSet(p,writing.fields.constructedWord.p,value);
});
const drum=miniClass('DrumHeads',{activeTarget:'System.Boolean'});
const hitDrum=method(drum.c,'DrumHeadSelect',0);
miniHook('DrumHeads','Update',0,args=>{
  if(get(args[0],drum.fields.activeTarget))invoke(hitDrum,args[0]);
});
// Score once when a note enters its target; the same object is reused next cycle.
const pianoNote=miniClass('PianoNote',{noteInTarget:'System.Boolean',parentNoteDropper:'PianoNoteDropper'});
const pressPiano=method(cls('PianoNoteDropper'),'PressPianoButton_PERFORMED',0);
const pianoSeen=new Set();
miniHook('PianoNote','OnTriggerEnter2D',1,null,(ret,state)=>{
  const p=state.object,key=p.toString();
  if(!get(p,pianoNote.fields.noteInTarget)||pianoSeen.has(key))return;
  const parent=p.add(pianoNote.fields.parentNoteDropper.offset).readPointer();
  if(alive(parent)){
    pianoSeen.add(key);invoke(pressPiano,parent);
  }
});
hooks.push(Interceptor.attach(method(pianoNote.c,'OnTriggerExit2D',1).readPointer(),{
  onEnter(args){this.note=args[0];},
  onLeave(){try{if(!get(this.note,pianoNote.fields.noteInTarget))pianoSeen.delete(this.note.toString());}catch(e){if(miniEnabled())fault(e);}}
}));

const college=miniClass('MG_CollegeManager',{chosenLessonWordIndex:'System.Int32',lessonYourScore:'System.Int32',lessonSuccessLimitScore:'System.Int32'});
miniHook('MG_CollegeManager','GiveAnswer',1,args=>{
  const answer=get(args[0],college.fields.chosenLessonWordIndex);
  if(answer>=0&&answer<4)args[1]=ptr(answer);
  const target=get(args[0],college.fields.lessonSuccessLimitScore);
  if(target>=0&&target<=10000)put(args[0],college.fields.lessonYourScore,Math.max(target,get(args[0],college.fields.lessonYourScore)));
});
const classMeter=field(college.c,'classPassMeterValue','System.Int32');
miniHook('MG_CollegeManager','FINISHED_NEW_LESSON',0,args=>{
  put(args[0],classMeter,Math.max(15,get(args[0],classMeter)));
});
const lock=miniClass('MG_LockpickManager',{lockpickTime:'System.Boolean',unlockAngle:'System.Single',eulerAngle:'System.Single'});
miniHook('MG_LockpickManager','Update',0,args=>{
  if(get(args[0],lock.fields.lockpickTime))put(args[0],lock.fields.eulerAngle,get(args[0],lock.fields.unlockAngle));
});

// Helpers below advance only activities already started by the player.
function pulse(cn,activeName,actionName,turnName){
  const fields={[activeName]:'System.Boolean'};if(turnName)fields[turnName]='System.Int32';
  const info=miniClass(cn,fields),action=method(info.c,actionName,turnName?1:0);
  const nextByObject=new Map();
  miniHook(cn,'Update',0,args=>{
    const p=args[0],key=p.toString(),now=Date.now();
    if(!get(p,info.fields[activeName])||now<(nextByObject.get(key)||0))return;
    nextByObject.set(key,now+160);
    if(nextByObject.size>100)nextByObject.clear();
    const values=turnName?[get(p,info.fields[turnName])]:[];
    invoke(action,p,values);
  });
}
pulse('MG_BathManager','bathTime','UsingBath_CONTROLLER','bathRightLeftTurn');
pulse('MG_TreadmillManager','treadmillTime','RunOnTreadmill_CONTROLLER','liftRightLeftTurn');
pulse('MG_BenchPressManager','benchPressTime','LiftWeight_CONTROLLER','liftRightLeftTurn');

const unbox=api('object_unbox','pointer',['pointer']);
const sliderActions=new Map();
function fullSlider(p){
  if(!alive(p))return;
  const c=A.objectClass(p),key=c.toString();
  if(!sliderActions.has(key))sliderActions.set(key,{max:method(c,'get_maxValue',0),set:method(c,'set_value',1)});
  const m=sliderActions.get(key),result=invoke(m.max,p);
  if(result.isNull())return;
  const maximum=unbox(result).readFloat();
  if(!Number.isFinite(maximum)||maximum<=0||maximum>1000000)return;
  const value=Memory.alloc(4);value.writeFloat(maximum);
  const args=Memory.alloc(PS);args.writePointer(value);
  const error=Memory.alloc(PS);error.writePointer(NIL);
  A.invoke(m.set,p,args,error);
  if(!error.readPointer().isNull())throw new Error('Falha ao completar a barra do minigame.');
}
const progressActivities=[
  ['MG_CookingManager','cookingTime',['progressSlider']],
  ['MG_KneadManager','kneadingTime',['kneadProgressSlider']],
  ['MG_CleanManager','cleaningTime',['cleanSlider']],
  ['MG_ToiletManager','toiletTime',['toiletProgressSlider']],
  ['MG_SingingManager','singingTime',['singProgressSlider','performanceSingSlider']],
].map(([name,active,sliders])=>{
  const fields={[active]:'System.Boolean'};
  for(const s of sliders)fields[s]='UnityEngine.UI.Slider';
  return {info:miniClass(name,fields),active,sliders};
});
let lastMiniMaintenance=0;
function minigameMaintenance(){
  if(!miniEnabled()||Date.now()-lastMiniMaintenance<120)return;
  lastMiniMaintenance=Date.now();
  capturePong();
  for(const {info,active,sliders} of progressActivities){
    const p=miniObject(info);
    if(p.isNull()||!get(p,info.fields[active]))continue;
    for(const s of sliders)fullSlider(p.add(info.fields[s].offset).readPointer());
  }
}

const pong=miniClass('PongManager',{startedGame:'System.Boolean',pongBall:'UnityEngine.GameObject',playerScore:'System.Int32',playerScoreText:'TMPro.TextMeshProUGUI'});
let pongOrigin=null;
const objectMethods=new Map();
function objectMethod(p,name,argc){
  const c=A.objectClass(p),key=c.toString()+':'+name+':'+argc;
  if(!objectMethods.has(key))objectMethods.set(key,method(c,name,argc));
  return objectMethods.get(key);
}
function transformOf(p){return invoke(objectMethod(p,'get_transform',0),p);}
function invokeValue(m,p,value){
  const args=Memory.alloc(PS);args.writePointer(value);
  const error=Memory.alloc(PS);error.writePointer(NIL);
  A.invoke(m,p,args,error);
  if(!error.readPointer().isNull())throw new Error('O minigame recusou a atualização.');
}
function capturePong(){
  const p=miniObject(pong);
  if(p.isNull()||!get(p,pong.fields.startedGame)){pongOrigin=null;return;}
  const ball=p.add(pong.fields.pongBall.offset).readPointer();
  if(!alive(ball))return;
  const transform=transformOf(ball);
  if(!alive(transform))return;
  if(pongOrigin&&pongOrigin.transform.equals(transform))return;
  const box=invoke(objectMethod(transform,'get_position',0),transform);
  if(box.isNull())return;
  const v=unbox(box),xyz=[v.readFloat(),v.add(4).readFloat(),v.add(8).readFloat()];
  if(xyz.every(Number.isFinite))pongOrigin={transform,xyz};
}
const newString=api('string_new','pointer',['pointer']);
// A missed Pong bounce is returned to its starting point and counted once.
// If no safe starting point was captured, preserve the original game's behavior.
hitProbe('PongBall',0xa5187b,'test','al, al',c=>{
  if((c.eax.toUInt32()&255)===0||!pongOrigin||!alive(pongOrigin.transform))return;
  const p=miniObject(pong);if(p.isNull()||!get(p,pong.fields.startedGame))return;
  const currentBall=p.add(pong.fields.pongBall.offset).readPointer();
  if(!alive(currentBall)||!transformOf(currentBall).equals(pongOrigin.transform))return;
  const xyz=Memory.alloc(12);pongOrigin.xyz.forEach((v,i)=>xyz.add(i*4).writeFloat(v));
  invokeValue(objectMethod(pongOrigin.transform,'set_position',1),pongOrigin.transform,xyz);
  c.eax=ptr(0);
  const score=get(p,pong.fields.playerScore);
  if(score>=0&&score<1000000){
    put(p,pong.fields.playerScore,score+1);
    const label=p.add(pong.fields.playerScoreText.offset).readPointer();
    if(alive(label)){
      // runtime_invoke takes reference arguments directly, unlike value arguments.
      const args=Memory.alloc(PS);args.writePointer(newString(str(''+(score+1))));
      const error=Memory.alloc(PS);error.writePointer(NIL);
      A.invoke(objectMethod(label,'set_text',1),label,args,error);
    }
  }
},'OnTriggerExit2D');
