// Hello World message
function callMyFunction() {
  console.log("This is working")
}

// TODO: in socket.on("update") turn the prefix (used in updateProgress) into
//  the "name" property
// TODO: replace updateSplit with updateProgress somehow

var socket = io();

socket.on("server-answer", function(message) {})

socket.on("update", function(json){
  if(json["name"] == "split") {
    return updateSplit(json)
  }

  if(json["name"] == "fft") {
    return updateProgress(json, "fft-")
  }

  if(json["name"] == "peak") {
    return updateProgress(json, "peak-")
  }

  if(json["name"] == "score") {
    return updateProgress(json, "score-")
  }
})

function updateSplit(json) {
  frame = document.getElementById("split")
  text  = document.getElementById("split-percent")
  bar   = document.getElementById("split-bar")

  if(json["count"] == 0) {
    text.innerHTML = "Gathering informations..."
    bar.setAttribute("style", "width: 0%")

    return
  }

  var progress  = json["data"][0]["progress"]
  var total     = json["data"][0]["total"]

  if(progress == 0 && total == 0) {
    text.innerHTML = "Awaiting worker..."
    bar.setAttribute("style", "width: 0%")
  } else if(progress == total) {
    text.innerHTML = "File split in " + total.toString() + " segments"
    bar.setAttribute("style", "width: 100%")
  } else {
    text.innerHTML = "In progress: " + progress.toString() + " out of " + total.toString()
    bar.setAttribute("style", "width: " + (100*progress/total).toFixed(0) + "%")
  }
}

// Shows or hide the the progress bar displaying "Gathering informations..."
//  in accordance to the worker job status
function showOrHideWaitbar(json, prefix) {
  bar = document.getElementById(prefix + "wait")

  if(json["count"] == 0) {
    bar.style.display = "block"
  } else {
    bar.style.display = "none"
  }
}

// Returns (create if necessary) the progress bar for the worker job status
//  identified by "prefix-order"
function getOrCreateProgressbar(prefix, order) {
  frame = document.getElementById(prefix + order.toString())

  if(!frame) {
    parent = document.getElementById(prefix + "parent")
    template = document.getElementById(prefix + "template")

    frame = addOrderedChild(parent, template, "order", order)

    frame.id = prefix + order.toString()
    frame.style.display = "block"
  }

  return frame
}

// Updates the pogress bar associated to a worker category
function updateProgress(json, prefix) {
  showOrHideWaitbar(json, prefix)

  json["data"].forEach(function(data) {
    var order			= data["order"]
    var status    = data["status"]
    var progress 	= data["progress"]
    var total			= data["total"]

    frame = getOrCreateProgressbar(prefix, order)
    text  = frame.children[0]
    bar   = frame.children[1]

    /* Update the progress bar */
    if(status == "created") {
      text.innerHTML = order.toString() + ": Awaiting worker"
      bar.setAttribute("style", "width: 0%")
    } else if(status == "started") {
      text.innerHTML = order.toString() + ": " + (100*progress/total).toFixed(1) + "%"
      bar.setAttribute("style", "width: " + (100*progress/total).toFixed(0) + "%")
    } else if (status == "completed") {
      text.innerHTML = order.toString() + ": Complete"
      bar.setAttribute("style", "width: 100%")
    }
  })
}

function addOrderedChild(parent, template, orderAttributeName, order) {
  var child = document.createElement(template.nodeName)

  child.classList.add(template.classList)
  // TODO: hardcoded "order" should be orderAttributeName
  child.setAttribute("order", order.toString())
  child.style.display = "block"
  child.innerHTML     = template.innerHTML

  var inserted = null

  for(i = 0; i < parent.children.length; i++) {
    otherOrder = parseInt(parent.children[i].getAttribute(orderAttributeName))

    if(order < otherOrder) {
      parent.insertBefore(child, parent.children[i])
      inserted = true
      break
    }
  }

  if(!inserted) {
    parent.appendChild(child)
  }

  return child
}
