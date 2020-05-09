/*
Purpose
This lets you create issues in a Jira project. This can be used to clone the Clover project or create our own
designed data.

Instructions
Paste this into a browser developer console when you are on the domain of a jira project

Status
This should run.

Source
Harun Delic
*/

// CHANGE THIS TO YOUR PROJECT KEY
let PROJECT_KEY = 'TEST'; 

// Some clover issues..
let data = {
  "issues": [
    {
      "summary": "Improve memory usage during instrumentation",
      "description": "The MethodSignature is holding onto references to CloverToken for too long during instrumentation, causing an excess use of memory. \r\n\r\nThis causes OOME for extremely large projects, especially running on a 64bit jvm.\r\n\r\n",
      "issuetype": "Suggestion",
      "assignee": "npellow",
      "resolution": "Fixed"
    },
    {
      "summary": "Disable unique coverage calculation at the project level until we have a marketing story for that",
      "description": "Unique coverage causes performance problems and we don't do that in Eclipse.\r\n",
      "issuetype": "Suggestion",
      "resolution": "Fixed"
    },
    {
      "summary": "Add cajo in acknowledgements and licenses",
      "issuetype": "Suggestion",
      "resolution": "Fixed"
    },
    {
      "summary": "Unable to use clover setup on generated classe",
      "description": "Hi,\r\n\r\nI try to use clover2:setup to instrument a jar. This jar contains some generated classes produced by maven jaxb plugin. \r\nHowever those classes are generated in a lifecycle phase after the instrumentation phase, so they are skipped. \r\n\r\nI've attached a simple project to demonstrate the problem. \r\n\r\nIf you try :\r\n\r\n{code}\r\nmvn clean install  -Dmaven.test.skip -o\r\n\r\n[INFO] [clover2:instrumentInternal]\r\n\r\n....\r\n\r\n[INFO] Clover all over. Instrumented 1 file (1 package).\r\n[INFO] 1 test method detected.\r\n[INFO] Elapsed time = 0,047 secs. (21,277 files/sec, 595,745 srclines/sec)\r\n...\r\n[INFO] [jaxb2:generate {execution: default}]\r\n[INFO] Succesfully generated output to: D:\\Developpement\\checkout\\cloverMPExported\\jar1\\target\\clover\\generated-sources\\xjc\r\n...\r\n{code}\r\n\r\nThe clover plugin is configured like that :\r\n\r\n{code:xml}\r\n            <plugin>\r\n                <groupId>com.atlassian.maven.plugins</groupId>\r\n                <artifactId>maven-clover2-plugin</artifactId>\r\n\t\t\t\t<version>2.5.0</version>\r\n                <configuration>\r\n                    <flushPolicy>threaded</flushPolicy>\r\n                    <flushInterval>100</flushInterval>\r\n                     <licenseLocation>${clover.licenseLocation}</licenseLocation>\r\n                </configuration>\r\n                <executions>\r\n                    <execution>\r\n                        <id>main</id>\r\n                        <phase>verify</phase>\r\n                        <goals>\r\n                            <goal>instrument</goal>\r\n                            <goal>aggregate</goal>\r\n                            <goal>check</goal>\r\n                            <goal>log</goal>\r\n                        </goals>\r\n                    </execution>\r\n                    <execution>\r\n                        <id>site</id>\r\n                        <phase>pre-site</phase>\r\n                        <goals>\r\n                            <goal>instrument</goal>\r\n                            <goal>aggregate</goal>\r\n\r\n                            <!-- We save a history point in order to have data to generate a historical report -->\r\n                            <goal>save-history</goal>\r\n\r\n                        </goals>\r\n                    </execution>\r\n                </executions>\r\n            </plugin>\r\n{code}\r\n\r\n\r\n",
      "issuetype": "Suggestion",
      "assignee": "npellow",
      "resolution": "Fixed"
    },
    {
      "summary": "Expand and add sub-sections to the  'Clover-for-Maven 2 User's Guide'; add 'Installation Guide' & 'Upgrade Guide'",
      "description": "Re-named this new page: http://confluence.atlassian.com/display/CLOVER/Maven+2+Clover+Plugin\r\n...to this: http://confluence.atlassian.com/display/CLOVER/Clover-for-Maven+2+User%27s+Guide\r\n\r\n TO DO: re-work / break into sub-sections\r\n TO DO: add Installation Guide\r\n TO DO: add Upgrade Guide",
      "issuetype": "Suggestion",
      "resolution": "Obsolete"
    },
    {
      "summary": "Please document instructions for integrating Clover with Eclipse PDE builds",
      "description": "h1. Assumptions:\r\n\r\na) 1 or more plugin projects\r\nb) 1 or more feature projects\r\nc) 1 project used to drive the build which may or may not contain customized xml files e.g. allElements.xml, customTargets.xml\r\nd) 1 or more test plugin projects using JUnit to run the tests \r\ne) 1 or more test feature projects\r\nf) Building is achieved through the headless PDE build system\r\ng) You build your plugins against an Eclipse installation that has the Clover-for-Eclipse plugins installed and you have input a valid Clover license.\r\nh) Testing is achieved through the Eclipse Test Framework\r\ni) You test your plugins by creating a fresh Eclipse installation and overlaying your plugins and features (including test plugins and features) and launching the Eclipse Test Framework test application.\r\n\r\nh1. General approach:\r\n\r\nThe first and most important aspect of the approach is the interception of the generation of all build.xmls for plugins & features. When this happens, I perform an XSLT transformation on plugin build.xmls which inserts a single clover task call just before the javac call. E.g.:\r\n{code}\r\n<clover-setup enabled=\"true|false\" initstring=\"/path/to/initstring\"/>\r\n{code}\r\n\r\nThis allows Clover to instrument before compilation.\r\n\r\nThe last aspect of the approach invokes the Clover HTML report at the end of the test run. This is the easiest part.\r\n \r\nh1. Example workspace setup:\r\n\r\nMy example workspace is based off the RCP quickstart project (http://rcpquickstart.com/2008/08/04/updated-pde-build-and-test-example/). The workspace is structured as follows:\r\n\r\ncom.rcpquickstart.helloworld (main plugin)\r\ncom.rcpquickstart.helloworld.build-ant-test (build project)\r\ncom.rcpquickstart.helloworld.feature (main feature)\r\ncom.rcpquickstart.helloworld.test (test plugin)\r\ncom.rcpquickstart.helloworld.test.feature (test feature)\r\n\r\nh1. Steps to get this working for your build\r\n\r\n1. Add the following to the build.properties of the build project\r\n\r\n{code}\r\nclover.enabled=true\r\n# Where the instrumentation database and coverage recordings are put\r\nclover.initstring=${buildDirectory}/.clover/coverage.db\r\n# Where HTML/XML/PDF reports are put\r\nclover.reportdir=${buildDirectory}/coverage-reports\r\n# Version of com.cenqua.clover.eclipse.ant\r\nclover.version=2.4.3.v20090309110000\r\n# Location of clover jar\r\nclover.jar=${eclipseLocation}/plugins/com.cenqua.clover.ant_${clover.version}/clover-eclipse-ant.jar\r\n{code}\r\n\r\n2. Add buildWithClover.xsl to the build project\r\n\r\n{code}\r\n<xsl:stylesheet version=\"1.0\" xmlns:xsl=\"http://www.w3.org/1999/XSL/Transform\">\r\n\t<xsl:param name=\"initstring\" expression=\"no_initstring_supplied\"/>\r\n\t<xsl:param name=\"enabled\" expression=\"false\"/>\r\n\t<xsl:template match=\"node()|@*\">\r\n\t   <xsl:copy>\r\n\t   <xsl:apply-templates select=\"@*\"/>\r\n\t   <xsl:apply-templates/>\r\n\t   </xsl:copy>\r\n\t </xsl:template>\r\n\t <xsl:template match=\"javac\">\r\n\t\t<clover-setup initstring=\"{$initstring}\" enabled=\"{$enabled}\"/>\r\n\t\t<xsl:copy>\r\n\t\t\t<xsl:apply-templates select=\"@* | node()\" />\r\n\t\t</xsl:copy>\r\n\t </xsl:template>\r\n</xsl:stylesheet>\r\n{code}\r\n\r\n3. In the build project, add or edit customTargets.xml. If this file doesn't exist, take a copy from ECLIPSE_PDE_INSTALLATION/org.eclipse.pde.build_X.Y.Z/templates/headless-build\r\nAdd this macrodef somewhere within the <project></project> element:\r\n\r\n{code}\r\n\t<macrodef name=\"cloverizeBuildXml\">\r\n\t\t<attribute name=\"file\"/>\r\n\t\t<sequential>\r\n\t\t\t<xslt in=\"@{file}\" out=\"@{file}.out\" style=\"${buildDirectory}/plugins/com.rcpquickstart.helloworld.build-and-test/buildWithClover.xsl\">\r\n\t\t\t\t<param name=\"initstring\" expression=\"${clover.initstring}/\"/>\r\n\t\t\t\t<param name=\"enabled\" expression=\"${clover.enabled}\"/>\r\n\t\t\t</xslt>\r\n\t\t\t<move file=\"@{file}.out\" tofile=\"@{file}\"/>\r\n\t\t</sequential>\r\n\t</macrodef>\r\n{code}\r\n\r\nEdit the postGenerate target as follows:\r\n\r\n{code}\r\n\t<target name=\"postGenerate\">\r\n\t\t<!-- repeat this for as many plugins as you want coverage for -->\r\n\t\t<cloverizeBuildXml file=\"${buildDirectory}/plugins/com.rcpquickstart.helloworld/build.xml\"/>\r\n\t\t<cloverizeBuildXml file=\"${buildDirectory}/plugins/com.rcpquickstart.helloworld.test/build.xml\"/>\r\n\t\t<antcall target=\"clean\" />\r\n\t</target>\r\n{code}\r\n\r\n5. Add this to the build project build.xml to invoke the Clover HTML report:\r\n{code}\r\n\t<target name=\"clover.report\">\r\n\t\t<!-- Set up Clover location and instrumentation path -->\r\n\t\t<taskdef resource=\"cloverlib.xml\" classpath=\"${clover.jar}\"/>\r\n\r\n\t\t<!-- \r\n\t\t\tProduce coverage analysis docs using Clover \r\n\t\t-->\r\n\t\t<clover-report failonerror=\"false\" initstring=\"${clover.initstring}\">\r\n\t       <current outfile=\"${clover.reportdir}\">\r\n\t          <format type=\"html\"/>\r\n\t       </current>\r\n\t\t</clover-report>\r\n\t</target>\r\n{code}\r\n \r\n6. You may not always want to run a code coverage build (e.g. you may want to toggle it by a property supplied through Bamboo). In that case you will need a few more build project build.xml changes to rewrite build.properties before it is used. Rewriting the build.properties is required because the labyrinthine RCP build system ignores properties specified on the command line and takes them from build.properties directly.\r\n\r\nSo in the build project build.properties, make clover.enabled=false instead of true\r\nNow rename build.properties to build.properties.base (this will have to be a permanent change w.r.t. for this project)\r\nAdd the following to the very top of the build project build.xml just after the <project ... > element\r\n\r\n{code}\r\n        <!-- ensure clover.enabled is always set to something -->\r\n\t<condition property=\"clover.enabled\" value=\"${clover.enabled}\" else=\"false\">\r\n\t\t<isset property=\"clover.enabled\"/>\r\n\t</condition>\r\n\t\r\n\t<copy file=\"build.properties.base\" tofile=\"build.properties\"/>\r\n\t<propertyfile file=\"build.properties\">\r\n\t\t<entry key=\"clover.enabled\" value=\"${clover.enabled}\"/>\r\n\t</propertyfile>\t\r\n{code}\r\n\r\nThis will ensure that Clover compilation is enabled/disabled depending on the value you supply to ant for clover.enabled. E.g. ant -Dclover.enabled=true build.xml clean init test clover.report \r\n\r\n----\r\n\r\nOne thing I forgot to mention is that you need to ensure whatever is hosting your unit tests as they run (presumably some Eclipse instance) makes the Clover jar available to the running instrumented tests / plugins. This can be done by ensuring the following is added to the launch line of whatever is running your tests (presumably in the build project's build.xml):\r\n\r\n{code}\r\n-Xbootclasspath/a:${clover.jar}\r\n{code}\r\n\r\n----\r\n\r\nHere's the Clover-enabled RCP Quickstart project. As I don't have access to a Linux machine I've kept it as is (configured for OSX) but there shouldn't be any major differences with your setup.\r\n\r\nProperties specific to my setup:\r\n\r\n{code}\r\npdeBuildPluginVersion=3.4.1.R34x_v20081217\r\nequinoxLauncherPluginVersion=1.0.101.R34x_v20081125\r\n# the Eclipse instance you're compiling against\r\nbase=/Users/michaelstudman/Projects/Cenqua/Eclipse/Installs/Eclipse_3.4.2PDE\r\n# the Eclipse instance used to drive compilation\r\neclipseLocation=/Users/michaelstudman/Projects/Cenqua/Eclipse/Installs/Eclipse_3.4.2PDE\r\n# the platform you wish to build for, you will probably want something like linux, gtk, x86\r\nconfigs=macosx, carbon, x86\r\n# where the build results go\r\nbuildDirectory=${user.home}/eclipse.build\r\n# my eclipse installations don't look like \"Eclipse_3.4.2PDE/eclipse/[plugins|features|...]\"  but rather \"Eclipse_3.4.2PDE/[plugins|features|...]\" so this is the same as ${base}\r\nbaseLocation=${base}\r\n{code}\r\n\r\nI have not zipped up the fresh Eclipse archive (eclipse-rcp-ganymede-SR2-macosx-carbon-1.tar.gz) I used to build the Eclipse instance to  run the tests as this is too large. You will need to download a version appropriate for your own platform, put in com.rcpquickstart.helloworld.build-and-test and then update build.xml accordingly. I have included the eclipse-test-framework-3.4.2.zip \r\n",
      "issuetype": "Suggestion",
      "resolution": "Fixed"
    },
    {
      "summary": "document historydir attribute in clover-check",
      "description": "re: CLOV-178\r\nif the user specifies the historydir attribute in clover-check, the project, and all specified packages will be checked against the previous historypoint (using the version of the current db, not just taking the latest historypoint)",
      "issuetype": "Suggestion",
      "resolution": "Fixed"
    },
    {
      "summary": "Update Maven doco to reflect that Maven 2.0.5 or later is required",
      "description": "I was playing with the Clover Maven plugin for the first time and came across this bug:\r\n\r\n[INFO] Internal error in the plugin manager executing goal 'org.apache.maven.plugins:maven-clover-plugin:2.4.1:instrumentInternal': Unable to find the mojo 'org.apache.maven.plugins:maven-clover-plugin:2.4.1:instrumentInternal' in the plugin 'org.apache.maven.plugins:maven-clover-plugin'\r\n\r\nhttps://support.atlassian.com/browse/CLV-4630\r\nhttps://support.atlassian.com/browse/CLV-4696\r\n\r\nEffectively maven was ignoring my ~/.mv2/settings.xml and locating the old clover plugin on maven central. The release notes for 2.0.5 fixed the following bug (not sure if it's the bug that was fixed however upgrading from 2.0.4 to 2.0.8 fixed the problem for me):\r\n\r\n[MNG-2236] - DefaultMavenProjectBuilder.buildStandaloneSuperProject() should include a ProfileManager that includes active profiles from settings.xml\r\n\r\nWe should work out if <2.0.5 is causing problems for us and document the minumum version of maven required if so.\r\n\r\nAssigning to you, Tom, to investigate and re-assign to Ed once you've clarified what's going on.",
      "issuetype": "Suggestion",
      "assignee": "npellow",
      "resolution": "Fixed"
    },
    {
      "summary": "Add a TestNG sanity Project",
      "description": "There has been a report of Clover incorrectly detecting TestNG test methods.\r\nIt appears to also cause the TestNG runner to run more methods which are not tests.\r\n\r\ne.g.\r\n{code}\r\n@BeforeTest\r\npublic void setup() throws Exception { \r\n    // code in here \r\n}\r\n\r\n@AfterTest\r\npublic void cleanUp() {\r\n    // code in here \r\n}\r\n{code}\r\n\r\nmay be run as tests once instrumented with Clover2.",
      "issuetype": "Suggestion",
      "assignee": "gcrain",
      "resolution": "Fixed"
    },
    {
      "summary": "Builds Fail with errors relating to JVM memory settings when entries for clover are put in a projects parent pom file.",
      "description": "We have created an organisational pom file which includes a profile called bamboo which contains the entries required to use clover. When we run a build in bamboo we set the maven goal to test site -Pbamboo, so that the profile is activated. The idea behind this is so that bamboo can generate clover reports for all projects and developers can still build projects on their workstations, without the need for clover licenses on every workstation, only a single license on the development server on which bamboo runs would be required.\r\n\r\nHowever, since upgrading to version 3.0 beta 5 of the maven clover plug in, builds fail when the above approach is taken, but build successfully when the clover entries are put directly into the project pom file.",
      "issuetype": "Suggestion",
      "assignee": "tom@atlassian.com",
      "resolution": "Fixed"
    },
    {
      "summary": "Document new per-package clouds in HTML reports",
      "description": "We need to update this page to document the new per-package clouds: http://confluence.atlassian.com/display/CLOVER/About+%27Coverage+Clouds%27\r\n\r\nYou may want to check with Brendan and Nick to ensure they are happy with the current implementation (you're on the review but it might be quicker just to ask them).\r\n\r\nText to be changed to:\r\n======\r\n'Coverage Clouds' provide an instant overview of your entire project and individual packages, enabling you to identify areas of your code that pose the highest risks or shortcomings.Each Coverage Cloud displays two metrics per Java Class. One metric is displayed via the font size, and the other via the font color. Each attribute has relative weighting across the entire project. Classes are sorted alphabetically. \r\n\r\n...\r\n\r\nProject Risks / Package Risks\r\n\r\nThe Project Risks / Package Risks Cloud highlights those classes that are the most complex, yet are the least covered by your tests. The larger and redder the class, the greater the risk that class poses for your project or package. Package risk clouds can be toggled to include or exclude classes in sub-packages\r\n\r\n...\r\n\r\nQuick Wins\r\n\r\nThis Cloud highlights the \"low hanging coverage fruit\" of your project or package. You will achieve the greatest increase in overall project or package coverage by covering the largest, reddest classes first. Package Quick Win clouds can be toggled to include or exclude classes in sub-packages.\r\n=====\r\n\r\nThe image currently shows the Eclipse plugin's clouds. We should instead show coverage clouds for Checkstyle or some other OSS project. A per-package (with sub packages toggle) and a per-project cloud should be shown.",
      "issuetype": "Suggestion",
      "resolution": "Fixed"
    },
    {
      "summary": "Don't spam the console with println anytime clover grails plugin is installed",
      "description": "From looking at the _Events.groovy hooks in the plugin, there are several println statements which will execute in all contexts, not just testing and not just when clover.on is specified. Specifically, the set classpath and compile start/end hooks will happen everytime any Grails command is run.\r\n\r\nThis is bad practice for a plugin. The println statements should be changed to use the grailsConsole which is available automatically\r\n\r\nprintln \"foo\" => grailsConsole.log \"foo\"\r\n\r\nor grailsConsole.updateStatus \"foo\"\r\n\r\nSecondly, this should probably be wrapped in a helper which only prints if the the clover is enabled, ie:\r\n\r\ndef logStuff(msg) {\r\n    if( config.on ) grailsConsole.log msg\r\n}",
      "issuetype": "Suggestion",
      "resolution": "Fixed"
    }
  ]
};

// NO NEED TO CHANGE THE BELOW:
let import_issue_meta_map = {};
let import_project_meta_map = {};
let issue_meta_list = [];

function json_request(method, successcode, endpoint, bodydata){
  return fetch(endpoint, {
    method: method,
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
    body: bodydata
  }).then(response => {
    const contentType = response.headers.get("content-type");
    if (contentType && contentType.indexOf("application/json") !== -1) {
      return response.json().then(jsondata => {
        if (response.status == successcode) {
          return jsondata;
        }
        else
          return Promise.reject(JSON.stringify(jsondata));
      })
    }
    else
      return Promise.reject(response);
  }).catch(err => console.error(err));
}

function DummyUser(){
  let self = this;
  self.accountId = undefined;
  
  self.get_dummy_user = function(){
    return json_request('GET', 200, '/rest/api/3/users/search').then(users => {
      let found = false;
      for (let user of users){
        if (user.displayName === "Dummy User"){
          found = true;
          self.accountId = user.accountId;
          break;
        }
      }

      if (!found)
        return self.make_dummy_user();
    });
 };

  self.make_dummy_user = function (){
    let bodyData = `{
      "password": "dummyuser123",
      "emailAddress": "dummy@user.invalid",
      "displayName": "Dummy User",
      "name": ""
    }`;
    return json_request('POST', 201, '/rest/api/3/user', bodyData).then(user => {
      self.accountId = user.accountId;
    });
  };
}

function Project(){
  let self = this;
  self.id = undefined;
  
  self.get_project = function (projectkey){
    return json_request('GET', 200, `/rest/api/3/project/${projectkey}`).then(project => {
      self.id = project.id;
    });
  };
}

function Projects(){
  let self = this;
  self.map = {};
  
  self.get_projects = function (){
    return json_request('GET', 200, `/rest/api/3/project`).then(projects => {
      for (let project of projects){
        self.map[project.name] = project.id;
      }
    });
  };
}

function IssueTypes(){
  let self = this;
  self.map = {};
  
  self.get_issuetypes = function (){
    return json_request('GET', 200, `/rest/api/3/issuetype`).then(issuetypes => {
      for (let issuetype of issuetypes){
        self.map[issuetype.name] = issuetype.id;
      }
    });
  };

}

function Resolutions(){
  let self = this;
  self.map = {};
  
  self.get_resolutions = function (){
    return json_request('GET', 200, `/rest/api/3/resolution`).then(resolutions => {
      for (let resolution of resolutions){
        self.map[resolution.name] = resolution.id;
      }
    });
  };

}

function Issue()
{
  let self = this;

  self.import_data = {
    id: undefined,
    key: undefined,
    link: undefined
  };

  self.issue_meta = {
    id: undefined,
    key: undefined,
    link: undefined
  };

  self.issue = {update:{}, fields:{}};
  self.update = {historyMetadata:{}, update:{}, fields:{}, properties:{}};

  self.set_import_id = function(importid){
    self.import_data.id = importid;
  };

  self.set_import_key = function(importkey){
    self.import_data.key = importkey;
  };

  self.set_import_link = function(importlink){
    self.import_data.link = importlink;
  };

  self.set_projectid = function (projectid){
    self.issue.fields.project = {id: projectid};
  };

  self.set_summary = function (summary){
    self.issue.fields.summary = summary;
  };

  self.set_issue_type = function (issuetype){
    self.issue.fields.issuetype = {id: issuetype};
  };

  self.set_resolution = function (resolution){
    self.issue.fields.resolution = {id: resolution};
  };

  self.set_description = function (description){
    self.issue.fields.description = {
      type: "doc",
      version: 1,
      content: [
        {
          type: "paragraph",
          content: [
            {
              text: description,
              type: "text"
            }
          ]
        }
      ]
    };
  };

  self.set_assignee = function (assignee){
    self.update.fields.assignee = {
      id: assignee
    };
  };

  self.set_priority = function (name){
    self.update.fields.priority = {
      name: name
    };
  };

  self.create_issue = function (){
    console.log(JSON.stringify(self.issue, null, 4));
    return json_request('POST', 201, '/rest/api/3/issue', JSON.stringify(self.issue)).then(issuemeta => {
      console.log(issuemeta);

      self.issue_meta = {
          id: issuemeta.id,
          key: issuemeta.key,
          link: issuemeta.self
      };

      issue_meta_list.push(self.issue_meta);
      
      if (typeof self.import_data.id !== 'undefined')
        import_issue_meta_map[self.import_data.id] = self.issue_meta;
      if (typeof self.import_data.key !== 'undefined')
        import_issue_meta_map[self.import_data.key] = self.issue_meta;
      if (typeof self.import_data.link !== 'undefined')
        import_issue_meta_map[self.import_data.link] = self.issue_meta;

      return self.update_issue();
    });
  };

  self.update_issue = function (){
    console.log(JSON.stringify(self.update, null, 4));
    return json_request('PUT', 204, `/rest/api/3/issue/${self.issue_meta.id}`, JSON.stringify(self.update)).then(issuemeta => {
            console.log(issuemeta);
    });
  };
}

function poptop(){
  if (data.issues.length > 0)
  {
    let d = data.issues[0];

    let issue = new Issue();
    issue.set_projectid(project.id);
    issue.set_assignee(dummyuser.accountId);
    
    //issue.set_import_id(d['id']);
    //issue.set_import_key(d['key']);
    //issue.set_import_link(d['link']);

    if ('description' in d)
      issue.set_description(d['description']);
    
    if ('issuetype' in d)
      if (d['issuetype'] in issuetypes.map)
        issue.set_issue_type(issuetypes.map[d['issuetype']]);
      else
        issue.set_issue_type(issuetypes.map['Task']);
    //issue.set_priority(data.issues['priority']);
    issue.set_priority('Medium');

    if ('summary' in d)
      issue.set_summary(d['summary']);
    //issue.set_resolution(resolutions.map["Done"]);
    data.issues.splice(0, 1);

    issue.create_issue().then(()=>{
      poptop();
    });
  }
}

let dummyuser = new DummyUser();
let project = new Project();
let issuetypes = new IssueTypes();
let resolutions = new Resolutions();

dummyuser.get_dummy_user().then(()=>{
  console.log("user: ", dummyuser.accountId);
  project.get_project(PROJECT_KEY).then(()=>{
    console.log("project: ", project.id);
    issuetypes.get_issuetypes().then(()=>{
      console.log("issuetypes: ", issuetypes.map);
      resolutions.get_resolutions().then(()=>{
        console.log("resolutions: ", resolutions.map);

        poptop();
      });
    });
  });
});

