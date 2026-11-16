// Basketball shot assistance hooks for To Pixelia v1.1.28 (Steam build 25632131).
// Project credit: n3urom4nc3r
function basketEnabled() {
  return !closed && Date.now() - lease <= 5000 && options.autoBasket;
}
function basketProbe(cn, mn, rva, mnemonic, operands, change) {
  const start = method(cls(cn), mn, 0).readPointer();
  const at = GAME.base.add(rva), distance = at.sub(start).toInt32();
  const ins = Instruction.parse(at);
  if (distance < 0 || distance > 0x3000 || ins.mnemonic !== mnemonic || ins.opStr !== operands)
    throw new Error('Verificação do basquete falhou: ' + cn + '.' + mn);
  hooks.push(Interceptor.attach(at, function() {
    if (!basketEnabled()) return;
    try { change(this.context); } catch (e) { fault(e); }
  }));
}
// These operands are local success thresholds, never the opponent's score or skill.
basketProbe('Player_Basketball', 'Player_ShotTaken', 0x60cb6e, 'movd', 'xmm0, edi', c => { c.edi = ptr(0x80000000); });
basketProbe('StreetBasketballPlayer', 'Player_ShotTaken', 0x52c79a, 'movd', 'xmm0, edi', c => { c.edi = ptr(0x80000000); });

// Receive panel commands even while a special basketball scene owns the updates.
for (const cn of ['Player_Basketball', 'StreetBasketballPlayer']) {
  hooks.push(Interceptor.attach(method(cls(cn), 'Update', 0).readPointer(), { onEnter() { frame(); } }));
}
