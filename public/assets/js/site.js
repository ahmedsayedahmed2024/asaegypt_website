(function(){
  var h=document.querySelector('.site-header');
  var forceSolid=h&&h.hasAttribute('data-solid');
  function onScroll(){ if(!h)return; if(forceSolid||window.scrollY>40){h.classList.add('solid')}else{h.classList.remove('solid')} }
  onScroll(); window.addEventListener('scroll',onScroll,{passive:true});

  var mn=document.querySelector('.mobile-nav');
  document.querySelectorAll('[data-open-menu]').forEach(function(b){b.addEventListener('click',function(){mn.classList.add('open');document.body.style.overflow='hidden';b.setAttribute('aria-expanded','true')})});
  document.querySelectorAll('[data-close-menu]').forEach(function(b){b.addEventListener('click',function(){mn.classList.remove('open');document.body.style.overflow='';})});

  document.querySelectorAll('.nav .has-dd>button').forEach(function(b){
    b.addEventListener('click',function(){var li=b.parentNode;var o=li.classList.toggle('open');b.setAttribute('aria-expanded',o)});
  });
  document.addEventListener('click',function(e){document.querySelectorAll('.nav .has-dd.open').forEach(function(li){if(!li.contains(e.target)){li.classList.remove('open');li.querySelector('button').setAttribute('aria-expanded','false')}})});

  var els=document.querySelectorAll('.rv');
  if('IntersectionObserver' in window){
    var io=new IntersectionObserver(function(en){en.forEach(function(x){if(x.isIntersecting){x.target.classList.add('in');io.unobserve(x.target)}})},{rootMargin:'0px 0px -8% 0px',threshold:.08});
    els.forEach(function(el){io.observe(el)});
  } else { els.forEach(function(el){el.classList.add('in')}); }

  document.querySelectorAll('.faq button').forEach(function(b){b.addEventListener('click',function(){var o=b.getAttribute('aria-expanded')==='true';b.setAttribute('aria-expanded',!o);b.nextElementSibling.hidden=o;})});

  // homepage "ASA Briefing" hexagon: the active bar's fill animation (6s) drives the rotation,
  // so pausing the animation (hover / keyboard focus) also pauses the rotation
  var br=document.getElementById('brief');
  if(br){
    var slides=br.querySelectorAll('.brief-slide'),bars=br.querySelectorAll('.bar'),live=br.querySelector('.brief-slides'),cur=0;
    var auto=!br.classList.contains('still');
    live.setAttribute('aria-live',auto?'off':'polite');
    var show=function(i){
      cur=(i+slides.length)%slides.length;
      slides.forEach(function(s,j){s.classList.toggle('on',j===cur)});
      bars.forEach(function(b,j){b.classList.remove('on');b.classList.toggle('done',j<cur);if(j===cur){b.setAttribute('aria-current','true')}else{b.removeAttribute('aria-current')}});
      void br.offsetWidth; // restart the fill animation
      bars[cur].classList.add('on');
    };
    bars.forEach(function(b,j){b.addEventListener('click',function(){show(j)})});
    if(auto){
      br.addEventListener('animationend',function(e){if(e.animationName==='bFill'&&br.classList.contains('run'))show(cur+1)});
      setTimeout(function(){br.classList.add('run')},br.classList.contains('intro')?2900:800);
      var hover=false,focus=false,upd=function(){br.classList.toggle('paused',hover||focus)};
      br.addEventListener('mouseenter',function(){hover=true;upd()});
      br.addEventListener('mouseleave',function(){hover=false;upd()});
      br.addEventListener('focusin',function(e){var fv=true;try{fv=e.target.matches(':focus-visible')}catch(x){}focus=fv;upd()});
      br.addEventListener('focusout',function(e){if(!br.contains(e.relatedTarget)){focus=false;upd()}});
    }
  }

  var y=document.querySelectorAll('[data-year]');y.forEach(function(e){e.textContent=new Date().getFullYear()});
})();
