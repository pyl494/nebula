/*
Purpose
This will be the basis of future work with the data. Our ML models will need a way to know which fields are useful
and which values to use for them. This data mapping will be the way to do that.

Status
This is a work-in-progress

Source
Harun Delic
*/

let data_map = {
    user: {
        ":<fields>": ['name', 'id'],
        //"someid": [{name: "other", id:"ids"},{name: "blah", id: "ok"}]
        //"somename": [{name: "", id:""}]
    },
    priority: {
        ":<fields>": ['name', 'id'],
        //"someid": [{id:"", name:""}]
        //"somename":[{id:"", name:""}]
    },
    fields: {
        ":<fields>": ['name', 'key', 'id'],
        //"someid": [{id: "", key: "", name: ""}]
        //"somekey": [{id: "", key: "", name: ""}]
        //"somename": [{id: "", key: "", name: ""}]
    }
};

let value_map = {
    priority: {
        "Highest": 5,
        "High": 4,
        "Medium": 3,
        "Low": 2,
        "Lowest": 1
    },
    user: {
        //"accountid": {ignore: false}
    },
    resolution: {
        "Done": {resolved: true, ignore: false},
        "Won't Do": {ignore: true},
        "Duplicate": {ignore: true},
        "Cannot Reproduce": {ignore: true},
    },
    issuetype: {
        "Bug": {bug: true},
        "Task": {work: true},
        "Change": {changerequest: true},
        "Feature": {featurerequest: true},
        "Story": {ignore: true}
    }
}

/*

useful jira fields:
issues.id
issues.key
issues.changelog....
1. issues.fields.issuetype {id/name/subtask}
1. issues.fields.project {id/key/name/projectTypeKey}
issues.fields.fixVersions
X 2. issues.fields.resolution
issues.fields.watches.watchCount
2. issues.fields.priority {name/id}
issues.fields.versions
X 2. issues.fields.issuelinks
2. issues.fields.assignee {displayName/accountId}
X 2. issues.fields.status {name/id}
X 2. issues.fields.status.statusCategory {id/key/name}
issues.fields.components
1. issues.fields.description
1. issues.fields.summary
X 2. issues.fields.creator {accountId/emailAddress/displayName/active}
issues.fields.subtasks
X 2. issues.fields.reporter {accountId/emailAddress/displayName/.}
X 2. issues.fields.environment
issues.fields.progress {progres/total}
issues.fields.aggregateprogress {progress/total}
issues.fields.votes {votes}

jira service desk fields:
issues.fields.customfield_10045("Time to done").ongoingCycle{startTime/breakTime/goalDuration/elapsedTime/remainingTime}
issues.fields.customfield_10046("Time to first response").ongoingCycle{..}

date times:
issues.fields.timespent
issues.fields.duedate
issues.fields.aggregatetimespent
issues.fields.resolutiondate
issues.fields.lastViewed
issues.fields.created
issues.fields.updated
issues.fields.timeestimate
issues.fields.aggregatetimeoriginalestimate
issues.fields.timeoriginalestimate


unknown:
issues.customfield_10027
issues.workratio
issues.fields.customfield_10020
issues.fields.customfield_10021
issues.fields.customfield_10022
issues.fields.customfield_10023
issues.fields.customfield_10024
issues.fields.customfield_10025
issues.fields.customfield_10026
issues.fields.customfield_10017
issues.fields.customfield_10018 {parent link?}
issues.fields.customfield_10019
*/

/*

Relationships:
case 1: ":<fields>": ['onefield'], {"value1": ["onefield":"value1"]}

1 to 1: it maps to itself
example: {"value1": [{"onefield":"value1"}]}

1 to 2: manually assigned mapping
example: 
{
    'user1' :[{'username': 'user1'}, {'username': 'user1_dev'}]
    'user1_dev' :[{'username': 'user1'}, {'username': 'user1_dev'}]
}

to avoid unnecessary duplication, manual assignment should be stored seperately in a concise form ?
{
    'user1': ['user1_dev'],
    'user1_dev': ['user1'],
}

===========

case 2: ":<fields>": ['field1', 'field2'], 
{
    'field1value1': [{'field1':'field1value1', 'field2':'field2value1'}],
    'field2value1': [{'field1':'field1value1', 'field2':'field2value1'}]
}

1 to 1: unique
{
    'field1value1': [{'field1':'field1value1', 'field2':'field2value1'}],
    'field2value1': [{'field1':'field1value1', 'field2':'field2value1'}]
}

1 to 2: commonality
{
    'field1value1': [
        {'field1':'field1value1', 'field2':'field2value1'}, 
        {'field1':'field1value1', 'field2':'field1value2'}
    ],
    'field2value1': [{'field1':'field1value1', 'field2':'field2value1'}]
    'field2value2': [{'field1':'field1value1', 'field2':'field2value2'}]
}

2 to 1: manually assigned mapping
{
    'field1value1': [
        {'field1':'field1value1', 'field2':'field2value1'},
        {'field1':'field1mappedvalue1', 'field2':'field2mappedvalue1'}
    ],
    'field2value1': [
        {'field1':'field1value1', 'field2':'field2value1'},
        {'field1':'field1mappedvalue1', 'field2':'field2mappedvalue1'}
    ]
    'field1mappedvalue1': [
        {'field1':'field1value1', 'field2':'field2value1'},
        {'field1':'field1mappedvalue1', 'field2':'field2mappedvalue1'}
    ],
    'field2mappedvalue2': [
        {'field1':'field1value1', 'field2':'field2value1'},
        {'field1':'field1mappedvalue1', 'field2':'field2mappedvalue1'}
    ]
}

concise assigned mapping:
{
    'field1value1': ['field1mappedvalue1'],
    'field2value1': ['field2mappedvalue2'],
    'field1mappedvalue1': ['field1value1'],
    'field2mappedvalue2': ['field2value1']
}

===

Analysis:

- When there is more than 1 field and there are unique mappings, that means that
you have values that can't automatically be linked to each other.

- When there is more than 1 field and there is commonality, that means you can
probably automatically map the fields to each other. Eg, (linking a user via user/email)

- Manual mappings are necessary, eg the unique mappings should be presented as a manual mapping case.
But there are also situations possible due to the custom fields, eg, if a project changes the standard 
priority scheme from High, Med, Low to Red, Orange, Green, then this can't be automatically determined.

*/