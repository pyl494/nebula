let timelineSizeShift = -(timelineSize * 1.0) / 2;
let cooldown = Date.now();

function doOnLoad(){
    let scrolls = document.getElementsByClassName('scroll-snap-container');

    for (let scroll of scrolls){
        console.log("ok");
        scroll.addEventListener('wheel', function(event){
            console.log(event);
            event.preventDefault();

            if (event.deltaY > 0)
            {
                scroll.scrollTop = scroll.scrollTop + timelineSize;
            }
            else if (event.deltaY < 0)
            {
                scroll.scrollTop = scroll.scrollTop - timelineSize;
            }
            
            return false;
        }, false);

    }
}

function zoomin(element){
    if (Date.now() - cooldown > 1100){
        let pRect = element.parentNode.getBoundingClientRect();
        pRect.x = (pRect.right + pRect.left) / 2.0;
        pRect.y = (pRect.bottom + pRect.top) / 2.0;

        let rect = element.getBoundingClientRect();
        rect.x = (rect.right + rect.left) / 2.0;
        rect.y = (rect.bottom + rect.top) / 2.0;

        element.className += ' timeline-node-active';
        
        element.parentNode.style.transform = `
            scale(${1})
            translate(
                ${document.body.clientWidth / 2 - rect.x * scale }px, 
                ${timelineSizeShift }px)
            `;
        element.parentNode.style.transformOrigin = `${0}px ${0}px`;/*`
                ${rect.x / (pRect.right - pRect.left)}% 
                ${rect.y / (pRect.bottom - pRect.top)}%`;*/
                element.parentNode.style.transition = 'transform 1s ease-in-out, transform-origin 1s linear';
        element.setAttribute('onclick', 'return zoomout(this);');

        cooldown = Date.now();
    }
    return false;
}

function zoomout(element){
    if (Date.now() - cooldown > 1100){
        let rect = element.getBoundingClientRect();

        element.className = element.className.replace(/\btimeline-node-active\b/g, "");

        element.parentNode.style.transform = `translate(0px, 0px) scale(${1/scale})`;
        element.parentNode.style.transformOrigin = `0px 0px`;
        element.parentNode.style.transition = 'transform 1s ease-in-out';
        element.setAttribute('onclick', 'return zoomin(this);');

        cooldown = Date.now();
    }
    return false;
}