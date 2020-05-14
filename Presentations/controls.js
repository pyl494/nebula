let timelineSizeShift = -(timelineSize * 0.9) / 2;
let cooldown = Date.now() + 10000000;
let nodeContents = [];

function doOnLoad(){
    makeDummies();
    hookContextMenu();
    cooldown = Date.now();
}

function hookContextMenu(){
    document.body.addEventListener('contextmenu', function(ev) {
        if (cooldown > 1100){
            ev.preventDefault();
            let active = document.getElementsByClassName('timeline-node-active');
            for (let element of active){
                zoomout(element, element.getAttribute('i'));
            }
        }
        return false;
    }, false);
}

function makeDummies(){
    let nodes = document.getElementsByClassName('timeline-node');
    let i = 0;
    for (let node of nodes) {
        node.setAttribute('i', i);
        node.setAttribute('onclick', `return zoomin(this, ${i});`);
        ++i;

        let contents = node.getElementsByClassName('timeline-content');
        let c = "";
        
        for (let content of contents){
            c += content.outerHTML;
        }

        nodeContents.push(c);
    }

    for (let node of nodes) {
        deleteContents(node);
    }
}

function deleteContents(element){
    let contents = element.getElementsByClassName('timeline-content');
    
    for (let content of contents){
        element.removeChild(content);
    }
}

function scrollFix(element){
    let scrolls = element.getElementsByClassName('scroll-snap-container');

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

function zoomin(element, i){
    if (Date.now() - cooldown > 1100){

        let pRect = element.parentNode.getBoundingClientRect();
        pRect.x = (pRect.right + pRect.left) / 2.0;
        pRect.y = (pRect.bottom + pRect.top) / 2.0;

        let rect = element.getBoundingClientRect();
        rect.x = (rect.right + rect.left) / 2.0;
        rect.y = (rect.bottom + rect.top) / 2.0;  

        element.parentNode.style.transform = `
            translateZ(0)
            scale(${1})
            translate(
                ${document.body.clientWidth / 2 - rect.x * scale /*- (document.body.clientWidth - (rect.right - rect.left) * scale ) / 2*/ }px, 
                ${timelineSizeShift }px)
            `;
            
        setTimeout(function(){
            element.parentNode.style.transform = `
                translateZ(0) 
                scale(${1})
                translate(
                    ${document.body.clientWidth / 2 - (element.offsetLeft + (document.body.clientWidth ) / 2)}px, 
                    ${timelineSizeShift }px)
            `;

            element.classList.add('timeline-node-active');
            element.setAttribute('onclick', '');

            setTimeout(function(){
                element.innerHTML += nodeContents[i];

                setTimeout(function(){
                    element.classList.add('timeline-node-show-content');

                    cooldown = Date.now();
                }, 600);

                scrollFix(element);

                cooldown = Date.now();
            }, 500);

            cooldown = Date.now();
        }, 1000);

        cooldown = Date.now();
    }
    return false;
}

function zoomout(element, i){
    if (Date.now() - cooldown > 1100){
        element.setAttribute('onclick', `return zoomin(this, ${i});`);
        
        element.classList.remove('timeline-node-show-content');

        setTimeout(function(){
            element.parentNode.style.transform = `
                translateZ(0) 
                scale(${1})
                translate(
                    ${document.body.clientWidth / 2 - (element.offsetLeft + timelineSize / 2)}px, 
                    ${timelineSizeShift }px)
            `;
            element.classList.remove('timeline-node-active');

            setTimeout(function(){
                element.parentNode.style.transform = `translateZ(0) translate(0px, 0px) scale(${1/scale})`;
    
                deleteContents(element);

                cooldown = Date.now();
            }, 1000);

            cooldown = Date.now();
        }, 600);

        
        cooldown = Date.now();
    }
    return false;
}