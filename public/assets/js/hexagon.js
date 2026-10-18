// ASA Hexagon (/hexagon/): the hero diagram's animation and its hover / tap highlights.
// The SVG is drawn at build time in its finished state (src/hexagon.py); this script plays the intro once
// (about 6.5 s, the approved timings) and then lets a corner or a balance line highlight its balance.
// With reduced motion the finished diagram is shown at once. Both layouts (wide, narrow) are driven together.
(function(){
  var hero=document.getElementById('hxg');if(!hero)return;
  var svgs=[].slice.call(hero.querySelectorAll('svg.hxd'));
  var msgs=[].slice.call(hero.querySelectorAll('.hxg-msg'));
  var replay=hero.querySelector('.hxg-replay');
  var reduce=window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches;
  var PAIR={1:2,2:1,3:4,4:3,5:6,6:5};
  var clamp=function(x){return Math.max(0,Math.min(1,x))};
  var eo=function(t){return 1-Math.pow(1-t,3)};
  var eio=function(t){return t<.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2};
  var back=function(t){var c1=1.9,c3=c1+1;return 1+c3*Math.pow(t-1,3)+c1*Math.pow(t-1,2)};
  var prog=function(t,s,d){return clamp((t-s)/d)};
  var num=function(el,a){return parseFloat(el.getAttribute(a))};
  var set=function(el,a,v){el.setAttribute(a,v)};
  function mix(a,b,t){var pa=parseInt(a.slice(1),16),pb=parseInt(b.slice(1),16);
    var r=Math.round(((pa>>16)&255)*(1-t)+((pb>>16)&255)*t),g=Math.round(((pa>>8)&255)*(1-t)+((pb>>8)&255)*t),bl=Math.round((pa&255)*(1-t)+(pb&255)*t);
    return '#'+((1<<24)+(r<<16)+(g<<8)+bl).toString(16).slice(1)}

  // one record per SVG: its elements and their finished values (read from the markup)
  var D=svgs.map(function(s){
    var q=function(c){return s.querySelector(c)},qa=function(c){return [].slice.call(s.querySelectorAll(c))};
    var glow='url(#'+q('filter').id+')';
    var rect=function(c,v){var r=q(c);if(!r)return null;var a=v?['y','height']:['x','width'];return {el:r,a:a,c:num(r,a[0])+num(r,a[1])/2,len:num(r,a[1])}};
    var verts={};
    qa('.hxd-v').forEach(function(g){var dot=g.querySelector('.hxd-dot');
      verts[g.getAttribute('data-n')]={g:g,dot:dot,ring:g.querySelector('.hxd-ring'),flash:g.querySelector('.hxd-flash'),lbl:g.querySelector('.hxd-lbl'),
        nm:[].slice.call(g.querySelectorAll('.hxd-nm')),x:num(dot,'cx'),y:num(dot,'cy'),k:+g.getAttribute('data-k'),focused:false}});
    return {svg:s,glow:glow,verts:verts,haze:q('.hxd-haze'),outline:q('.hxd-outline'),sidesG:q('.hxd-sides'),
      sides:qa('.hxd-side').map(function(g){var l=g.querySelectorAll('line');return {l:l,len:num(l[0],'stroke-dasharray'),spark:g.querySelector('circle')}}),
      stripes:qa('.hxd-s'),stripesG:q('.hxd-stripes'),
      beams:[q('.hxd-btop'),q('.hxd-bmid'),q('.hxd-bbot')],
      clips:[rect('.hxd-rtop'),rect('.hxd-rmid'),rect('.hxd-rbot')],ax:rect('.hxd-rax',true),
      bals:qa('.hxd-bal'),halo:q('.hxd-halo'),cring:q('.hxd-cring'),trust:qa('.hxd-tr')};
  });
  var start=0,raf=0,done=false;

  function grow(r,p){if(r){set(r.el,r.a[0],r.c-r.len/2*p);set(r.el,r.a[1],r.len*p)}}

  function draw(d,t){
    var n,v;
    // 1. corners pop in, 1 to 6, each with an expanding ring (0–1.1 s)
    for(n=1;n<=6;n++){v=d.verts[n];var s=(n-1)*110,p=prog(t,s,450),q=prog(t,s,700);
      var sc=p>0?back(p):0;
      set(v.dot,'transform','translate('+v.x+' '+v.y+') scale('+sc+') translate('+(-v.x)+' '+(-v.y)+')');
      set(v.ring,'r',8+28*eo(q));set(v.ring,'opacity',q>0&&q<1?.9*(1-q):0)}
    // 2. each side grows from its middle towards its two corners (0.75–1.85 s)
    d.sides.forEach(function(sd,j){var st=750+j*70,p=eio(prog(t,st,850));
      set(sd.l[0],'stroke-dashoffset',sd.len*(1-p));set(sd.l[1],'stroke-dashoffset',sd.len*(1-p));
      var sp=prog(t,st-60,180);set(sd.spark,'opacity',sp>0&&sp<1?Math.sin(sp*Math.PI):0)});
    // a corner flashes white once when its two sides reach it, so the outline "locks"
    for(n=1;n<=6;n++){v=d.verts[n];var prev=(v.k+5)%6,arrive=Math.max(750+v.k*70,750+prev*70)+850,f=prog(t,arrive-40,520);
      set(v.flash,'opacity',f>0&&f<1?Math.sin(f*Math.PI)*.95:0);set(v.flash,'r',10+16*f)}
    var allIn=prog(t,2050,400);
    set(d.outline,'opacity',allIn);set(d.sidesG,'opacity',1-allIn);
    // 3. the names come down, flash lime and settle to white, 1 to 6 (2.05–3.4 s)
    for(n=1;n<=6;n++){v=d.verts[n];var s3=2050+(n-1)*170,p3=eo(prog(t,s3,560)),g=prog(t,s3+260,700);
      set(v.lbl,'opacity',p3);set(v.lbl,'transform','translate(0 '+(-16*(1-p3))+')');
      if(!v.focused)v.nm.forEach(function(el){el.style.fill=g<1?mix('#C3D648','#FFFFFF',g):'';
        if(g>0&&g<.6)set(el,'filter',d.glow);else el.removeAttribute('filter')})}
    // 4. the 12 stripes connect one after another, then settle to a faint background (3.3–5.4 s)
    d.stripes.forEach(function(s4,i){var p4=eo(prog(t,3300+i*80,420)),settle=prog(t,4500,900);
      set(s4,'opacity',p4*(.95-(.95-.13)*settle))});
    set(d.haze,'opacity',.03*prog(t,3300,1200));
    // 5. balances: the middle line from the centre outwards, then the top and bottom lines; their names fade in
    grow(d.clips[1],eio(prog(t,4500,650)));grow(d.clips[0],eio(prog(t,4800,600)));grow(d.clips[2],eio(prog(t,4950,600)));
    var rtl=document.documentElement.dir==='rtl';
    [1,0,2].forEach(function(b,i){var el=d.bals[b];if(!el)return;var p5=eo(prog(t,4700+i*220,600));
      set(el,'opacity',p5);set(el,'transform','translate('+((rtl?14:-14)*(1-p5))+' 0)')});
    // 6. trust: the axis, the centre circle, then the word(s) with a soft glow (5.4–6.7 s)
    grow(d.ax,eio(prog(t,5400,700)));
    var pc=prog(t,5900,450),pw=eo(prog(t,6050,500));
    set(d.cring,'opacity',pc);set(d.cring,'r',Math.max(.01,12*(pc>0?back(pc):0)));
    set(d.halo,'opacity',.35*pc);
    d.trust.forEach(function(el){set(el,'opacity',pw)});
  }

  function frame(now){
    var t=reduce?1e6:now-start;
    svgs.forEach(function(s,i){draw(D[i],t)});
    hero.classList.remove('hxg-pre');
    if(t<6900){raf=requestAnimationFrame(frame)}else finish();
  }
  function finish(){done=true;svgs.forEach(function(s){s.classList.add('alive')});hero.classList.remove('hxg-run')}

  // highlight pillar n's balance (both corners, their names, the balance line and label) and dim the rest;
  // 0 clears it (inline styles removed, so the animation's own values apply again)
  function show(n){
    var bi=n?Math.floor((n-1)/2):-1,op=function(on,dim){return n?(on?1:dim):''};
    D.forEach(function(d){
      for(var k=1;k<=6;k++){var v=d.verts[k],pair=!!n&&(k===n||k===PAIR[n]);
        v.focused=pair;
        v.g.style.opacity=op(pair,.28);
        v.nm.forEach(function(el){el.style.fill=pair?'#C3D648':''});
        set(v.dot,'r',pair?11:8)}
      d.bals.forEach(function(el,i){el.style.opacity=op(i===bi,.25)});
      d.beams.forEach(function(el,i){el.style.opacity=n?(i===bi?.95:.15):''});
      d.stripesG.style.opacity=n?.5:'';
    });
    msgs.forEach(function(m){m.classList.toggle('on',+m.getAttribute('data-b')===bi)});
  }
  function focus(n){if(done)show(n)}
  D.forEach(function(d){
    // hover with a mouse; a tap (click) selects, and a tap elsewhere clears (touch screens fire no reliable hover)
    var bind=function(el,n){
      el.addEventListener('pointerenter',function(e){if(e.pointerType==='mouse')focus(n)});
      el.addEventListener('pointerleave',function(e){if(e.pointerType==='mouse')focus(0)});
      el.addEventListener('click',function(e){e.stopPropagation();focus(n)});
    };
    for(var k=1;k<=6;k++)bind(d.verts[k].g,k);
    [].forEach.call(d.svg.querySelectorAll('.hxd-hit'),function(h){bind(h,+h.getAttribute('data-n'))});
  });
  document.addEventListener('click',function(){focus(0)});

  function play(){
    cancelAnimationFrame(raf);done=false;show(0);
    svgs.forEach(function(s){s.classList.remove('alive')});
    hero.classList.add('hxg-run');
    start=performance.now();raf=requestAnimationFrame(frame);
  }
  if(reduce){frame(0);return}
  if(replay){replay.hidden=false;replay.addEventListener('click',function(e){e.stopPropagation();play()})}
  // start once the fonts are in (the names are measured by the browser), or after 1 s at the latest
  var go=false,begin=function(){if(!go){go=true;play()}};
  if(document.fonts&&document.fonts.ready)document.fonts.ready.then(begin);
  setTimeout(begin,1000);
})();
