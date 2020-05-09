/*
Purpose
This is the old version. It uses the 'xml export' to dump the data from jira projects.

Instructions
Paste this into a browser developer console when you are on the domain of a jira project

Status
This should run.

Source
Harun Delic
*/

if(typeof(String.prototype.trim) === "undefined")
{
    String.prototype.trim = function() 
    {
        return String(this).replace(/^\s+|\s+$/g, '');
    };
}

function getpage(data, pagesRemaining, page){
    if (pagesRemaining.length > 0)
    {
        let target = pagesRemaining[0];
        console.log('GET', target.project, page);
        // https://jira.atlassian.com/rest/api/2/search?jql=ORDER%20BY%20priority%20DESC%2C%20updated%20DESC&validateQuery=false&maxResults=1000&startAt=0
        let query = encodeURIComponent(`ORDER BY priority DESC, updated DESC`);
        let req = new Request(`${target.baseurl}jira.issueviews:searchrequest-xml/temp/SearchRequest.xml?jqlQuery=${query}&tempMax=1000&pager/start=${page}`);
        fetch(req)
            .then(response => {
                console.log(response.status, response.statusText);
                if (response.status == 200)
                {
                    return response;
                }
                else
                {
                    console.log('DONE', target.project, page);
                    pagesRemaining.splice(0, 1);
                    getpage('', pagesRemaining, 0);
                    return Promise.reject('done');
                }
            })
            .then(response => response.blob())
            .then(blob => blob.text())
            .then(text => {
                console.log('SAVING', target.project, page);
                downloaddata(text, target.project + '_' + page.toString());
                getpage('', pagesRemaining, page + 1000);
            }).catch((error)=>{
                console.log('ERROR', target.project, page);
                console.log(error);
                pagesRemaining.splice(0, 1);
                getpage('', pagesRemaining, 0);
            })
    }
};

let pull = function(pages)
{
    getpage('', pages, 0);
}

function downloaddata(data, name){
    var file = new Blob([data], {type: 'text/xml'});
    var a = document.createElement("a"),
    url = URL.createObjectURL(file);
    a.href = url;
    a.download = `${name}.xml`;
    document.body.appendChild(a);
    a.click();
    setTimeout(function() {
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);  
    }, 0); 
};

pull([{
    baseurl: 'https://issues.apache.org/jira/sr/',
    project: 'APACHE'
}])

pull([{
    baseurl: 'https://jira.atlassian.com/sr/',
    project: 'ATLASSIAN'
}])

pull([{
    baseurl: 'https://tngtech-oss.atlassian.net/sr/',
    project: 'TNGTECH'
}])

//https://jira.sakaiproject.org/rest/api/2/search?issuetype%20%3D%20%27Feature%20Request%27