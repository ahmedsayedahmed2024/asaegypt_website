const React=require('react');const RDS=require('react-dom/server');const fa=require('react-icons/fa6');
const names=process.argv.slice(2);const out={};
for(const n of names){ if(!fa[n]){console.error('missing',n);continue;} out[n]=RDS.renderToStaticMarkup(React.createElement(fa[n],{size:'1em'})).replace(/ height="1em" width="1em"/,'').replace('<svg ','<svg aria-hidden="true" ');}
require('fs').writeFileSync('src/icons.json',JSON.stringify(out));console.log(Object.keys(out).length);
