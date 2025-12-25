#########################################
# Please do not delete this section below.
# Created By: Nam Nguyen Hoai.
# Created Date: Aug-2025
# Version: 3.0
#########################################
from enum import Enum
from datetime import datetime, timezone
UTC = timezone.utc
import subprocess
import tempfile
import csv, os, re, sys
import optparse
from collections import defaultdict
#########################################


# VARIABLES
# TEMP_DATA_FILE = tempfile.gettempdir() + "\\data.xml"
# TEMP_COOKIE_FILE = tempfile.gettempdir() + "\\cookie.txt"
TEMP_DATA_FILE = os.path.join(tempfile.gettempdir(), "data.xml")
TEMP_COOKIE_FILE = os.path.join(tempfile.gettempdir(), "cookie.txt")

SEPARATOR = ";"


#########################################
class Entries(Enum):
    URL = "https://rationalcld.dl.net/"
    CONTEXT = "qm/"
    SERVICE_URL = "service/com.ibm.rqm.integration.service.IIntegrationService/resources/"
    URN_ID = "urn:com.ibm.rqm:<resource_name>:<resource_id>"
    CONFIG_CONTEXT = "?oslc_config.context=" + (URL + "gc/configuration/").replace(":", "%3A").replace("/", "%2F") + "<stream_id>"    
    RESOURCE_URL_WITHOUT_GC = URL + CONTEXT + SERVICE_URL + "<project_area>/<resource_name>/"
    RESOURCE_URL = RESOURCE_URL_WITHOUT_GC + CONFIG_CONTEXT
    URN_RESOURCE_URL_WITHOUT_GC = RESOURCE_URL_WITHOUT_GC + URN_ID
    URN_RESOURCE_URL = URN_RESOURCE_URL_WITHOUT_GC + CONFIG_CONTEXT
    VERSION = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
    HEADER = "xmlns:ns2=\"http://jazz.net/xmlns/alm/qm/v0.1/\" xmlns:ns1=\"http://www.w3.org/1999/02/22-rdf-syntax-ns#\" xmlns:ns3=\"http://schema.ibm.com/vega/2008/\" xmlns:ns4=\"http://purl.org/dc/elements/1.1/\" xmlns:ns5=\"http://jazz.net/xmlns/prod/jazz/process/0.6/\" xmlns:ns6=\"http://jazz.net/xmlns/alm/v0.1/\" xmlns:ns7=\"http://purl.org/dc/terms/\" xmlns:ns8=\"http://jazz.net/xmlns/alm/qm/v0.1/testscript/v0.1/\" xmlns:ns9=\"http://jazz.net/xmlns/alm/qm/v0.1/executionworkitem/v0.1\" xmlns:ns10=\"http://open-services.net/ns/core#\" xmlns:ns11=\"http://open-services.net/ns/qm#\" xmlns:ns12=\"http://jazz.net/xmlns/prod/jazz/rqm/process/1.0/\" xmlns:ns13=\"http://www.w3.org/2002/07/owl#\" xmlns:ns14=\"http://jazz.net/xmlns/alm/qm/qmadapter/v0.1\" xmlns:ns15=\"http://jazz.net/xmlns/alm/qm/qmadapter/task/v0.1\" xmlns:ns16=\"http://jazz.net/xmlns/alm/qm/v0.1/executionresult/v0.1\" xmlns:ns17=\"http://jazz.net/xmlns/alm/qm/v0.1/catalog/v0.1\" xmlns:ns18=\"http://jazz.net/xmlns/alm/qm/v0.1/tsl/v0.1/\" xmlns:ns20=\"http://jazz.net/xmlns/alm/qm/styleinfo/v0.1/\" xmlns:ns21=\"http://www.w3.org/1999/XSL/Transform\""
    NS2_RESOURCE_OPEN_TAG = "<ns2:<resource_name> " + HEADER + ">"
    NS4_TITLE = "<ns4:title><title></ns4:title>"
    NS4_DESCRIPTION = "<ns4:description><description></ns4:description>"
    NS2_CATEGORY = "<ns2:category term=\"<category_name>\" value=\"<category_value>\"/>"
    NS2_RESOURCE_LINK = "<ns2:<resource_name> href=\"<resource_url>\"/>"
    NS18_RESOURCE_LINK = "<ns18:<resource_name> href=\"<resource_url>\"/>"
    NS2_STATE_LABEL = "<ns2:stateLabel><status_label></ns2:stateLabel>"
    NS6_STATE = "<ns6:state><status></ns6:state>" 
    DETAILS_LINK = "<p><a href=\"<link_path>\"><link_name></a></p>"
    DETAILS_CLOSE_TAG = "</div></details>"
    DETAILS_OPEN_TAG = "<details xmlns=\"http://jazz.net/xmlns/alm/qm/v0.1/executionresult/v0.1\"><div xmlns=\"http://www.w3.org/1999/xhtml\">"
    NS2_RESOURCE_CLOSE_TAG = "</ns2:<resource_name>>"
    # AUTHENTICATE_COMMAND = "curl -d \"j_username=<user_name>\" -d \"j_password=<password>\" \"" + URL + CONTEXT + "j_security_check\" -c \"<cookie_file>\" -s -i"
    # CREATE_COMMAND = "curl -b \"<cookie_file>\" --data @<data_xml_file> \"<url>\" -s -i"
    # ATTACHMENT_COMMAND = "curl -b \"<cookie_file>\" -F \"data=@<attachment_file>\" \"<url>\" -s -i"
    # GET_COMMAND = "curl -b \"<cookie_file>\" -X GET \"<url>\" -s"
    AUTHENTICATE_COMMAND = "curl -k -L -d \"j_username=<user_name>\" -d \"j_password=<password>\" \"" + URL + CONTEXT + "j_security_check\" -c \"<cookie_file>\" -s -i"
    CREATE_COMMAND = "curl -k -L -b \"<cookie_file>\" --data @<data_xml_file> \"<url>\" -s -i"
    ATTACHMENT_COMMAND = "curl -k -L -b \"<cookie_file>\" -F \"data=@<attachment_file>\" \"<url>\" -s -i"
    GET_COMMAND = "curl -k -L -b \"<cookie_file>\" -X GET \"<url>\" -s"
    PASSED = "com.ibm.rqm.execution.common.state.passed"
    FAILED = "com.ibm.rqm.execution.common.state.failed"
    BLOCKED = "com.ibm.rqm.execution.common.state.blocked"
    PAUSED = "com.ibm.rqm.execution.common.state.paused"
    PERMFAILED = "com.ibm.rqm.execution.common.state.perm_failed"
    ERROR = "com.ibm.rqm.execution.common.state.error"
    INCOMPLETE = "com.ibm.rqm.execution.common.state.incomplete"
    INCONCLUSIVE = "com.ibm.rqm.execution.common.state.inconclusive"
    DEFFERED = "com.ibm.rqm.execution.common.state.deferred"
    

class ResponsesPatterns(Enum):
    STATUS_CODE_NUM = r"(?<=HTTP/1.1 )\d+"
    STATUS_CODE_FULL = r"(?<=HTTP/1.1 )[0-9A-Za-z ]+"
    CONTENT_LOCATION = r"(?<=Content-Location: )[0-9A-Za-z_/:\-]+"
    LOCATION = r"(?<=\nLocation: )[0-9A-Za-z_/:.\+\%\-]+"
    RESULT_ID = r"(?<=\<rqm:resultId xmlns:rqm\=\"http://schema.ibm.com/rqm/2007\#executionresult\"\>)\d+"


def getEntryValue(k):
    try:
        return getattr(Entries, k.upper()).value
        
    except:
        return ""

def parseCSVFile(csvFile):
    t = []
    if (len(csvFile) > 0 and os.path.exists(csvFile)):
        with open(csvFile, 'r', encoding="utf-8") as file:
            csv2dict = csv.DictReader(file)
            for i in csv2dict:                
                n = {}
                for k, v in i.items():
                    n[k.encode("ascii", "ignore").decode().replace("\"", "")] = v
                t.append(n)
    return t

def getKeysByValue(dictionary):    
    grouped_keys = defaultdict(list)
    for key, value in dictionary.items():
        grouped_keys[value].append(key)
    return grouped_keys

def getTestSuites(tcers):
    suiteIDs = set([x["Test Suite Execution Record ID"] for x in tcers if "Test Suite Execution Record ID" in x and x["Test Suite Execution Record ID"].isdigit()])
    r = {}
    for suiteID in suiteIDs:
        d = {}
        l = []
        totalPass = 0
        totalFail = 0
        totalBlock = 0
        totalTC = 0
        for tcer in tcers:
            currentSuiteID = tcer["Test Suite Execution Record ID"]            
            if currentSuiteID == suiteID:
                d["Suite ID"] = suiteID
                totalTC += 1
                d["Name"] = tcer["Test Suite Execution Records"]         
                
                tcerState = tcer["Last Result"] if "Last Result" in tcer else ''
                if tcerState == "Passed":
                    totalPass += 1
                elif tcerState == "Failed":
                    totalFail += 1
                elif tcerState == "Blocked":
                    totalBlock += 1

                l.append(tcer)
                d['Test Case Execution Records'] = l
        
        d["Total Pass"] = str(totalPass)
        d["Total Fail"] = str(totalFail)
        d["Total Block"] = str(totalBlock)
        d["Total Tests"] = str(totalTC)
        
        state = ""
        if totalBlock > 0:
            state = "Blocked"
        
        if len(state) == 0 and totalFail > 0:
            state = "Failed"
        
        if len(state) == 0 and totalTC == totalPass and totalPass > 0:
            state = "Passed"
        
        if len(state) == 0:
            state = "Incomplete"        
        d['State'] = state
               
        r[suiteID] = d
    return r

# def runCommand(command):
#     output = ""
#     if len(command) > 0:
#         proc=subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, )
#         output = proc.communicate()[0].decode() 
#         print("Output CMD: " + output)           
#     return output

def runCommand(command):
    if not command:
        return ""
    proc = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    out, err = proc.communicate()

    out = out.decode(errors="ignore")
    err = err.decode(errors="ignore")

    if err.strip():
        print("STDERR:", err)  # <-- NOW YOU CAN SEE REAL ERROR
    return out

def parseResponse(response):
    r = {}
    for item in ResponsesPatterns:
        k = item.name.lower().replace("_", " ")
        v = item.value
        value = ""
        m = re.search(v, response)
        if m is not None:
            value = m.group(0).strip()            
        r[k] = value    
    return r

def getProjectAreaAlias(projectArea):
    return projectArea.replace(" ", "+").replace("(", "%28").replace(")", "%29")

def generateServiceUrl(projectArea, streamID=None, resourceName="executionresult", resourceID=None):
    urnID = ""
    if resourceID is not None and len(resourceID) > 0:
        urnID = getEntryValue("URN_ID").replace("<resource_name>", resourceName).replace("<resource_id>", resourceID)
    cfgContext = ""
    if streamID is not None and len(streamID) > 0:
        cfgContext = getEntryValue("CONFIG_CONTEXT").replace("<stream_id>", streamID)
    
    URL = getEntryValue("RESOURCE_URL_WITHOUT_GC").replace("<resource_name>", resourceName).replace("<project_area>", getProjectAreaAlias(projectArea)) + urnID + cfgContext
    return URL

def generateTCRContent(tcerInfo, projectArea, streamID=""):    
    try:
        content = []
        content.append(getEntryValue("VERSION"))
        content.append((getEntryValue("NS2_RESOURCE_OPEN_TAG")).replace("<resource_name>", "executionresult"))
        
        # add title
        tcrName = tcerInfo["Name"] + "_" + datetime.now().strftime("%Y%m%d_%H%M%S")
        print("TCR Name: " + tcrName)
        content.append((getEntryValue("NS4_TITLE")).replace("<title>", tcrName))
        
        # add categories
        categories = [x for x in tcerInfo if "[Category]" in x]        
        for c in categories: content.append((getEntryValue("NS2_CATEGORY")).replace("<category_name>", c.replace("[Category]", "").strip()).replace("<category_value>", tcerInfo[c]))
        
        others = {}
        others["executionworkitem"] = tcerInfo["ID"]        
        if "Test Plan ID" in tcerInfo and len(tcerInfo["Test Plan ID"]) > 0: others["testplan"] = tcerInfo["Test Plan ID"]
        if "Test Case ID" in tcerInfo and len(tcerInfo["Test Case ID"]) > 0: others["testcase"] = tcerInfo["Test Case ID"]
        if "Build Record ID" in tcerInfo and len(tcerInfo["Build Record ID"]) > 0: others["buildrecord"] = tcerInfo["Build Record ID"]
        if "Test Script ID" in tcerInfo and len(tcerInfo["Test Script ID"]) > 0: others["remotescript"] = tcerInfo["Test Script ID"]        
        # Attachment ID k can thiet vi se tu dong upload len.
        if "Attachment ID" in tcerInfo and len(tcerInfo["attachment"]) > 0: others["attachment"] = tcerInfo["Attachment ID"]
        
        # add others resources
        for k, v in others.items():
            if len(v) > 0:
                resourceUrl = getEntryValue("RESOURCE_URL_WITHOUT_GC").replace("<project_area>", getProjectAreaAlias(projectArea)).replace("<resource_name>", k) + "urn:com.ibm.rqm:" + k + ":" + v
                content.append((getEntryValue("NS2_RESOURCE_LINK")).replace("<resource_url>", resourceUrl).replace("<resource_name>", k))
        
        # update state
        stateLabel = tcerInfo["Last Result"]
        if len(stateLabel) > 0:
            state = getEntryValue(stateLabel.upper())
            content.append((getEntryValue("NS2_STATE_LABEL")).replace("<status_label>", stateLabel))
            content.append((getEntryValue("NS6_STATE")).replace("<status>", state))        
        
        # Add attachment link
        if "Log Path" in tcerInfo and len(tcerInfo["Log Path"]) > 0:
            logPath = tcerInfo["Log Path"]
            logs = logPath.split(SEPARATOR)
            logs = [x.replace("&", "&amp;").strip() for x in logs]            

            attachmentResourceUrl = generateServiceUrl(projectArea, streamID, "attachment")
            if "Test Script ID" in tcerInfo and len(tcerInfo["Test Script ID"]) > 0:
                for l in logs:
                    print("Upload attachment: " + l)
                    attachmentCommand = getEntryValue("ATTACHMENT_COMMAND").replace("<attachment_file>", l).replace("<url>", attachmentResourceUrl).replace("<cookie_file>", TEMP_COOKIE_FILE)
                    attachmentResponse = runCommand(attachmentCommand)
                    attachmentLocation = parseResponse(attachmentResponse)["location"]                    
                    content.append((getEntryValue("NS2_RESOURCE_LINK")).replace("<resource_url>", attachmentLocation).replace("<resource_name>", "attachment"))                    
            else:                
                content.append(getEntryValue("DETAILS_OPEN_TAG"))                
                for l in logs:
                    print("Upload attachment: " + l)
                    attachmentCommand = getEntryValue("ATTACHMENT_COMMAND").replace("<attachment_file>", l).replace("<url>", attachmentResourceUrl).replace("<cookie_file>", TEMP_COOKIE_FILE)
                    attachmentResponse = runCommand(attachmentCommand)                    
                    attachmentLocation = parseResponse(attachmentResponse)["location"]                    
                    linkName = os.path.basename(l)
                    content.append(getEntryValue("DETAILS_LINK").replace("<link_path>", attachmentLocation).replace("<link_name>", linkName))
                
                content.append(getEntryValue("DETAILS_CLOSE_TAG"))
        
        content.append((getEntryValue("NS2_RESOURCE_CLOSE_TAG")).replace("<resource_name>", "executionresult"))
        return "".join(content)
    except:
        return ""

def generateTSRContent(suiteInfo, projectArea, suiteURL=None, testResults=[]):
    try:
        content = []        
        content.append(getEntryValue("VERSION"))
        content.append((getEntryValue("NS2_RESOURCE_OPEN_TAG")).replace("<resource_name>", "testsuitelog"))
        tserName = suiteInfo["Name"] if "Name" in suiteInfo else ''
        print("Test Suite Executon Record: " + tserName)
        tserName = tserName + "_" + datetime.now().strftime("%Y%m%d_%H%M%S")
        print("Test Suite Result Name: " + tserName)
        content.append((getEntryValue("NS4_TITLE")).replace("<title>", tserName))
        
        # update state
        stateLabel = suiteInfo["State"] if "State" in suiteInfo else ''
        if len(stateLabel) > 0:
            state = getEntryValue(stateLabel.upper())
            content.append((getEntryValue("NS2_STATE_LABEL")).replace("<status_label>", stateLabel))
            content.append((getEntryValue("NS6_STATE")).replace("<status>", state))        
        
        # update statistic        
        content.append(f"<ns18:testcasestotal>{suiteInfo['Total Tests']}</ns18:testcasestotal>")
        content.append(f"<ns18:testcasespassed>{suiteInfo['Total Pass']}</ns18:testcasespassed>")
        content.append(f"<ns18:testcasesfailed>{suiteInfo['Total Fail']}</ns18:testcasesfailed>")
        content.append(f"<ns18:testcasesblocked>{suiteInfo['Total Block']}</ns18:testcasesblocked>")
        
        # add start time and end time, if not set time, default start time will be 1970
        #curTime = datetime.utcnow().isoformat(timespec='milliseconds') + 'Z'
        curTime = str(datetime.now(UTC).now()).replace(' ', 'T') + 'Z'
        content.append(f"<ns18:starttime>{curTime}</ns18:starttime>")
        content.append(f"<ns18:endtime>{curTime}</ns18:endtime>")
        
        tcerDictList = suiteInfo['Test Case Execution Records']
        buildID = ""
        planID = ""
        # update elements
        content.append("<ns18:suiteelements>")
        index = 0
        for tcerDict in tcerDictList:
            content.append("<ns18:suiteelement>")            
            content.append(f"<ns18:index>{str(index)}</ns18:index>")            
            buildID = tcerDict["Build Record ID"]
            planID = tcerDict["Test Plan ID"]
            tcerid = tcerDict["ID"]
            tcid = tcerDict["Test Case ID"]
            scriptID = tcerDict["Test Script ID"]
            
            tcerURL = generateServiceUrl(projectArea, streamID=None, resourceName="executionworkitem", resourceID=tcerid)
            tcURL = generateServiceUrl(projectArea, streamID=None, resourceName="testcase", resourceID=tcid)
            content.append(f"<ns18:executionworkitem href=\"{tcerURL}\"/>")
            content.append(f"<ns18:testcase href=\"{tcURL}\"/>")            
            
            if len(scriptID) > 0:
                scriptURL = generateServiceUrl(projectArea, streamID=None, resourceName="remotescript", resourceID=scriptID)
                content.append(f"<ns18:remotescript href=\"{scriptURL}\"/>")
            
            index += 1
            
            content.append("</ns18:suiteelement>")
        content.append("</ns18:suiteelements>")        
        
        # update test case result
        for testResult in testResults:
            testResultURL = generateServiceUrl(projectArea, streamID=None, resourceName="executionresult", resourceID=testResult)
            content.append(f"<ns2:executionresult href=\"{testResultURL}\"/>")
        
        tserID = suiteInfo["Suite ID"]
        print(f"TSER ID: {tserID}")
        tserIDURL = generateServiceUrl(projectArea, streamID=None, resourceName="suiteexecutionrecord", resourceID=tserID)
        content.append(f"<ns2:suiteexecutionrecord href=\"{tserIDURL}\"/>")
        
        if suiteURL is not None:
            content.append(f"<ns2:testsuite href=\"{suiteURL}\"/>")
            
        planURL = generateServiceUrl(projectArea, streamID=None, resourceName="testplan", resourceID=planID)
        if len(planURL) > 0:
            content.append(f"<ns2:testplan href=\"{planURL}\"/>")
            
        # add build id and test plan id
        buildURL = generateServiceUrl(projectArea, streamID=None, resourceName="buildrecord", resourceID=buildID)
        if len(buildURL) > 0:
            content.append(f"<ns2:buildrecord href=\"{buildURL}\"/>")
        
        content.append((getEntryValue("NS2_RESOURCE_CLOSE_TAG")).replace("<resource_name>", "testsuitelog"))
        return "".join(content)
    except:
        return ""
    
def updateTSR(tcerInfoList, projectArea, streamID=None, resultDict=[]):
    if len(tcerInfoList) > 0:
        suiteInfoDict = getTestSuites(tcerInfoList)
        suitesIncResultDict = getKeysByValue(resultDict)
        
        if len(suiteInfoDict) > 0:                        
            # run all suite
            for k, v in suiteInfoDict.items():
                print("******************************************")
                tserURL = generateServiceUrl(projectArea, streamID, "suiteexecutionrecord", k)
                response = runCommand(getEntryValue("GET_COMMAND").replace("<url>", tserURL).replace("<cookie_file>", TEMP_COOKIE_FILE))
                
                # get suite
                suitePattern = r"(?<=\<ns2:testsuite href=\")[0-9A-Za-z_/:.\+\-]+"                        
                m = re.search(suitePattern, response)
                
                suiteURL = None
                if m is not None:
                    suiteURL = m.group(0)                    

                testResults = []
                if k in suitesIncResultDict: testResults = suitesIncResultDict[k]                

                if len(v) > 0:
                    tsrContent = generateTSRContent(v, projectArea, suiteURL, testResults)
                    f = open(TEMP_DATA_FILE,'w')
                    f.write(tsrContent)
                    f.close()
                    
                    serviceLink = generateServiceUrl(projectArea, streamID, "testsuitelog")
                    createCommand = getEntryValue("CREATE_COMMAND").replace("<data_xml_file>", TEMP_DATA_FILE).replace("<url>", serviceLink).replace("<cookie_file>", TEMP_COOKIE_FILE)
                    response = runCommand(createCommand)
                    responseDict = parseResponse(response)
                    statusCodeNum = responseDict["status code num"]
                    statusCodeFull = responseDict["status code full"]
                    
                    print(f"Status code full: {statusCodeFull}")
                    updateStatus = "FAIL"
                    if statusCodeNum in ["201", "200"]:
                        updateStatus = "PASS"
                    print(f"Update Suite Result Status: {updateStatus}")


def updateTCR(csvFile, projectArea, streamID, user, password, retries=1, resultFilter="All", exportOutputFile=False, updateSuite=False):
    try:
        if os.path.exists(csvFile):
            outputFile = ""
            if bool(exportOutputFile):
                outputFile = csvFile.replace(".csv", "_output_" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".csv")

            # remove existing cookie file to make sure no unexpected error
            if os.path.exists(TEMP_COOKIE_FILE): os.remove(TEMP_COOKIE_FILE)            
            
            # Login
            loginCommand = getEntryValue("AUTHENTICATE_COMMAND").replace("<user_name>", user).replace("<password>", password).replace("<cookie_file>", TEMP_COOKIE_FILE)
            loginResponse = runCommand(loginCommand)
            loginLocation = parseResponse(loginResponse)["location"]            
            # Login successfully
            if len(loginLocation) > 0 and "auth/authfailed" not in loginLocation:

                print("Login Successfully!!!!!")
                # get service link
                serviceLink = generateServiceUrl(projectArea, streamID, "executionresult")
                # parsing csv file
                tcerInfoList = parseCSVFile(csvFile)
                writeHeader = True
                resultDict = {}
                
                # Loop all tcers
                for tcerInfo in tcerInfoList:
                    run = True
                    if resultFilter.upper() != "ALL": run = tcerInfo["Last Result"] == resultFilter                    
                    if run:                    
                        print("******************************************")
                        print("TCER ID: " + tcerInfo["ID"])
                        print("TCER Name: " + tcerInfo["Name"])                        
                        # get tser id
                        tserID = tcerInfo["Test Suite Execution Record ID"]
                        
                        fd = None
                        if len(outputFile) > 0:
                            fd = open(outputFile, "a", encoding="utf-8")
                            if writeHeader:
                                headers = list(tcerInfo.keys())
                                headers.append("Upload Result Status")
                                headers.append("Status Code")
                                headers.append("Result ID")
                                headers.append("Retry Times")
                                fd.writelines(",".join(headers)+ "\n")
                                writeHeader = False
                        
                        # write data to temp file
                        tcrData = generateTCRContent(tcerInfo, projectArea, streamID)
                        f = open(TEMP_DATA_FILE,'w')
                        f.write(tcrData)
                        f.close()
                        
                        # get command
                        createCommand = getEntryValue("CREATE_COMMAND").replace("<data_xml_file>", TEMP_DATA_FILE).replace("<url>", serviceLink).replace("<cookie_file>", TEMP_COOKIE_FILE)
                        response = runCommand(createCommand)
                        responseDict = parseResponse(response)
                        statusCodeNum = responseDict["status code num"]
                        
                        uploadStatus = "FAIL"
                        # retry
                        i = 0
                        while (statusCodeNum not in ["201", "200"]) and i < int(retries):
                            print("Retry times: " + str(i))
                            
                            # login again if required
                            if "X-com-ibm-team-repository-web-auth-msg: authrequired" in response:                            
                                print("Login again because authentication required.")
                                loginResponse = runCommand(loginCommand)                            
                            
                            response = runCommand(createCommand)
                            responseDict = parseResponse(response)
                            statusCodeNum = responseDict["status code num"]
                            
                            i += 1                            
                        
                        if statusCodeNum in ["201", "200"]: uploadStatus = "PASS"
                        
                        statusCodeFull = responseDict["status code full"]
                        resultID = responseDict["result id"]
                        print("Status code full: " + statusCodeFull)
                        print("Result ID: " + resultID)
                        print("Upload Result Status: " + uploadStatus)
                        
                        if len(resultID) > 0:
                            resultDict[resultID] = tserID
                        
                        if fd is not None:
                            values = list(tcerInfo.values())
                            values.append(uploadStatus)
                            values.append(statusCodeNum)
                            values.append(resultID)
                            values.append(str(i))
                            
                            values = ["\"" + x + "\"" for x in values]
                            fd.writelines(",".join(values) + "\n")
                            fd.close()
            
                # run xong update test suite result
                if bool(updateSuite):
                    print("***** START UPDATING TEST SUITE RESULT *****")
                    updateTSR(tcerInfoList, projectArea, streamID, resultDict)  
                    print("***** END UPDATING TEST SUITE RESULT *****")
                
            # Login failed
            else:
                print("Login Unsuccessfully!!!!!")            
            
            # Delete temp file
            if os.path.exists(TEMP_DATA_FILE): os.remove(TEMP_DATA_FILE)
            if os.path.exists(TEMP_COOKIE_FILE): os.remove(TEMP_COOKIE_FILE)
            
            print("COMPLETED!!!")
        else:
            print(csvFile + " NOT EXIST.")
    
    except:
        print("Error: " + str(sys.exc_info()[1]).replace("\n", ""))


def cli():
    p = optparse.OptionParser(usage='usage: %prog [options] arguments')
    
    p.add_option('--filePath', '-f'
                 , dest="filePath"
                 , help="Refer Testcase_Execution_Template.csv. For example: ../Test_Execution_Record.csv")    
    
    p.add_option('--projectArea', '-a'
                 , default=None
                 , help="Project Area is the name of the project being logged into. Surround with double quotes if the name contains spaces. Example: \"HHS (Test)\"")
    
    p.add_option('--streamID', '-s'
                 , default=None
                 , help="It is stream ID. If user does not specify this argument, Jazz QM will use the initial stream.")
    
    p.add_option('--user', '-u'
                 , default=None
                 , help="Is a registered user ID within Jazz QM.")

    p.add_option('--password', '-p'
                 , default=None
                 , help="Is the password of the user used.")

    p.add_option('--retries', '-i'
                 , default=1
                 , help="Retries when fail uploading result. Default is 1")
    
    p.add_option('--resultFilters', '-r'
                 , default="All"
                 , help="Update test case result with specified status, such as Passed, Failed, ... Default value is All.")
    
    p.add_option('--exportOutputFile', '-o'
                 , default=False
                 , help="Export out put file the same folder with the given input file path. Default is False")

    p.add_option('--updateSuiteResult', '-q'
                 , default=False
                 , help="Update test suite result after updating test case execution records. Default is False")

    
    options, arguments = p.parse_args()
    
    if (not options.filePath):  # if filepath is not given
        p.error('File path is not given.')
               
    #if not stoprun:
    updateTCR(options.filePath
            , options.projectArea
            , options.streamID
            , options.user
            , options.password
            , options.retries
            , options.resultFilters
            , options.exportOutputFile
            , options.updateSuiteResult)

if __name__ == '__main__':
    cli()

