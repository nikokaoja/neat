

export function getSelectedWorkflowName() {
  let workflowName = localStorage.getItem("selectedWorkflowName");
  if (workflowName == null) {
    workflowName = "default";
  }
  return workflowName;
}
export function setSelectedWorkflowName(workflowName: string) {
  localStorage.setItem("selectedWorkflowName", workflowName);
}

export function getNeatApiRootUrl() {
  let url = localStorage.getItem("neatApiRootUrl");
  if (url == null) {
    // url = "http://localhost:8000";
    const protocol = window.location.protocol;
    const domain = window.location.hostname;
    const port = window.location.port;
    url = protocol + "//" + domain + ":" + port;
  }
  return url;
}

export function convertMillisToStr(millis) {
  const date = new Date(millis);
  const isoString = date.toISOString();
  return isoString;
}


export default function RemoveNsPrefix(strWithPrefix: string) {

  if (strWithPrefix.includes("#"))
  {
    const strPlit = strWithPrefix.split("#")
    if (strPlit.length > 1) {
      return strPlit[1]
    }
  }else if (strWithPrefix.includes("/")) {
    const strPlit = strWithPrefix.split("/")
    if (strPlit.length > 1) {
      return strPlit[strPlit.length-1]
    }
  }

  return strWithPrefix;
}
