from shapely.geometry import Polygon, box
from shapely import affinity
H, W, w = 58.0, 55.5, 25.5
k = (W - w) / H
hexa = Polygon([(-w,-H),(w,-H),(W,0),(w,H),(-w,H),(-W,0)])
top = hexa.intersection(box(-100,-100,100,-1.5))
def uband(a,b):  # a <= x + k y <= b
    return Polygon([(a-k*-100,-100),(b-k*-100,-100),(b-k*100,100),(a-k*100,100)])
def vband(a,b):  # a <= x - k y <= b
    return Polygon([(a+k*-100,-100),(b+k*-100,-100),(b+k*100,100),(a+k*100,100)])
TL=[top.intersection(uband(a,b)) for a,b in [(-55.5,-40.5),(-37.5,-22.5),(-19.5,-4.5)]]
right = top.intersection(uband(-1.5, 200))
TR=[right.intersection(vband(a,b)) for a,b in [(40,55.5),(22,37.5),(4,19.5)]]
rot=lambda g: affinity.rotate(g,180,origin=(0,0))
BR=[rot(g) for g in TL]; BL=[rot(g) for g in TR]
def path(g):
    polys = [g] if g.geom_type=='Polygon' else list(g.geoms)
    out=''
    for p in polys:
        c=list(p.exterior.coords)[:-1]
        out+='M'+' L'.join(f'{x:.2f} {y:.2f}' for x,y in c)+'Z'
    return out
def svg(cls='mark', animate=False, colors=('#80CAE3','#A6D8EE','#B2DCF2','#C3D648')):
    parts=[]
    i=0
    for grp,col,name in [(TL,colors[0],'tl'),(TR,colors[1],'tr'),(BR,colors[2],'br'),(BL,colors[3],'bl')]:
        for g in grp:
            parts.append(f'<path class="s s-{name}" style="--i:{i}" fill="{col}" d="{path(g)}"/>'); i+=1
    return f'<svg class="{cls}" viewBox="-56 -59 112 118" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'+''.join(parts)+'</svg>'
if __name__=='__main__':
    s=svg()
    open('dist/assets/img/mark.svg','w').write(s.replace('<svg class="mark" ','<svg '))
    print(len(s))
