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

  var y=document.querySelectorAll('[data-year]');y.forEach(function(e){e.textContent=new Date().getFullYear()});
})();
