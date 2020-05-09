/*
Purpose
This lets you dump the results of jira API calls

Instructions
Paste this into a browser developer console when you are on the domain of a jira project

Status
This should run.

Source
Harun Delic
*/

let fields = [
    '/rest/api/3/priority',
    '/rest/api/3/role',
    '/rest/api/3/resolution',
    '/rest/api/3/field',
    '/rest/api/3/issueLinkType',
    '/rest/api/3/issuesecurityschemes',
    '/rest/api/3/issuetype'
];


function getfield (fields)
{
  let next = function(fields)
  {
      fields.splice(0,1);
      getfield(fields)
  };

  if (fields.length > 0)
  {
    fetch(fields[0], {
      method: 'GET'
    })
      .then(response => {
        console.log(
          `Response: ${response.status} ${response.statusText}`
        );
        return response.text();
      })
      .then(text => {
        console.log(fields[0], text);
        next(fields);
      })
      .catch(err => {
        console.error(fields[0], err);
        next(fields);
      });
    }
}

getfield(fields);

