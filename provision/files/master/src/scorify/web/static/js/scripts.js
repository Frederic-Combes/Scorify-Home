// Makes the page dynamic

var socket = io();

// socket.on("connect", function(){
//   console.log("Subscribing...")
//   socket.emit("subscribe-to-hash", "{{ hash }}")
//
//   var intervalID = setInterval(function() {
//     socket.emit('request-update', "{{ hash }}")
//   }, 250)
// })
//
// socket.on("disconnect", function(msg){
//   console.log("On disconnect: " + msg)
//
//   if(intervalID) {
//     clearInterval(intervalID)
//     intervalID = null
//   }
// })

socket.on("server-answer", function(message) {
  // Debugging purpose only
  // console.log(message)
})

socket.on("update-split", function(json) {
  frame = document.getElementById("split")
  text  = document.getElementById("split-percent")
  bar   = document.getElementById("split-bar")

  var progress 	= json['progress']
  var total			= json['total']

  if(progress == 0 && total == 0) {
    text.innerHTML = "Awaiting worker"
    bar.setAttribute("style", "width: 0%")
  } else if(progress == total) {
    text.innerHTML = "File split in " + total.toString() + " segments"
    bar.setAttribute("style", "width: 100%")
  } else {
    text.innerHTML = "In progress: " + progress.toString() + " out of " + total.toString()
    bar.setAttribute("style", "width: " + (100*progress/total).toFixed(0) + "%")
  }
})

socket.on("update-fft", function(json) {
  if(Object.keys(json).length > 0) {
    frame = document.getElementById("fft-wait")

    if(frame) {
        frame.style.display = "none"
    }
  }

  allComplete = Object.keys(json).length > 0

  Object.keys(json).forEach(function(key) {
    frame = document.getElementById("fft-" + key)

    var order			= json[key]['order']
    var progress 	= json[key]['progress']
    var total			= json[key]['total']

    if(!frame) {
      parent   = document.getElementById("fft-parent")
      template = document.getElementById("fft-template")
      frame    = addOrderedChild(parent, template, "order", order)

      frame.id            = "fft-" + key
      frame.style.display = "block"
    }

    text  = frame.children[0]
    bar   = frame.children[1]


    if(progress == 0 && total == 0) {
      text.innerHTML = order.toString() + ": Awaiting worker"
      bar.setAttribute("style", "width: 0%")
      allComplete = false
    } else if(progress == total) {
      text.innerHTML = order.toString() + ": Complete"
      bar.setAttribute("style", "width: 100%")
    } else {
      text.innerHTML = order.toString() + ": " + (100*progress/total).toFixed(1) + "%"
      bar.setAttribute("style", "width: " + (100*progress/total).toFixed(0) + "%")
      allComplete = false
    }
  })

  if(allComplete) {
    Object.keys(json).forEach(function(key) {
      frame               = document.getElementById("fft-" + key)
      frame.style.display = "none"
    })

    frame               = document.getElementById("fft-complete")
    frame.style.display = "block"
  }
})


socket.on("update-peak", function(json){
  if(Object.keys(json).length > 0) {
    frame = document.getElementById("peak-wait")

    if(frame) {
        frame.style.display = "none"
    }
  }

  allComplete = Object.keys(json).length > 0

  Object.keys(json).forEach(function(key) {
    frame = document.getElementById("peak-" + key)

    var order			= json[key]['order']
    var progress 	= json[key]['progress']
    var total			= json[key]['total']

    if (!frame ) {
      parent   = document.getElementById("peak-parent")
      template = document.getElementById("peak-template")
      frame    = addOrderedChild(parent, template, "order", order)

      frame.id            = "peak-" + key
      frame.style.display = "block"
    }

    text  = frame.children[0]
    bar   = frame.children[1]

    if(progress == 0 && total == 0) {
      text.innerHTML = order.toString() + ": Awaiting worker"
      bar.setAttribute("style", "width: 0%")
      allComplete = false
    } else if(progress == total) {
      text.innerHTML = order.toString() + ": Complete (" + progress.toString() + " out of " + total.toString() + ")"
      bar.setAttribute("style", "width: 100%")
    } else {
      text.innerHTML = order.toString() + ": " + (100*progress/total).toFixed(1) + "%"
      bar.setAttribute("style", "width: " + (100*progress/total).toFixed(0) + "%")
      allComplete = false
    }
  })

  if(allComplete) {
    Object.keys(json).forEach(function(key) {
      frame               = document.getElementById("peak-" + key)
      frame.style.display = "none"
    })

    frame               = document.getElementById("peak-complete")
    frame.style.display = "block"
  }
})

function callMyFunction() {
  console.log("This is working")
}

function addOrderedChild(parent, template, orderAttributeName, order) {
  var child = document.createElement(template.nodeName)

  child.classList.add(template.classList)
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
