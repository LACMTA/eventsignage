def getSuffix(dayint):
    if (4 <= dayint <= 20) or (24 <= dayint <= 30):
        suffix = "th"
    else:
        suffix = ["st", "nd", "rd"][dayint % 10 - 1]
    return suffix


def getFloor(aroom):
    rooms = {
      "Interview Room 1":"01 Plaza",
      "Interview Room 2":"01 Plaza",
      "Interview Room 3":"01 Plaza",
      "Large Testing Room":"01 Plaza",
      "Interview Room 4":"01 Plaza",
      "Plaza Lobby Area":"01 Plaza",
      "West Patio":"01 Plaza",
      "Artesia":"2",
      "Customer Information":"2",
      "Systems Library (IT)":"2",
      "Boardroom":"3",
      "Henry Huntington":"3",
      "Board Conference Room":"3",
      "Gateway":"3",
      "Union Station":"3",
      "Cafe Lobby":"3",
      "3rd Floor Lobby":"3",
      "Plaza View":"4",
      "University":"4",
      "TAP Conference Room (4-67)":"4",
      "Ethics":"4",
      "Computer Room #1":"4",
      "Computer Room #2":"4",
      "University Conference Rm Patio":"4",
      "East Wing":"5",
      "Valencia":"5",
      "West Wing":"5",
      "Granada":"6",
      "Hastus Training Lab":"6",
      "San Marino":"7",
      "Scheduling":"7",
      "SPA":"7",
      "Arcadia":"8",
      "Pacific":"8",
      "Palisades":"8",
      "Alhambra":"9",
      "Wilshire":"9",
      "Riviera":"10",
      "Heritage":"13",
      "Rail Center":"13",
      "Employee and Labor Relations":"14",
      "Irvine":"14",
      "Olympic":"14",
      "Woodland Hills 14-77":"14",
      "William Mulholland":"15",
      "Library (Open Area)":"15",
      "Catalina":"16",
      "Burbank":"17",
      "Silverlake":"18",
      "Art and Design Studio Conference Room":"19",
      "Palos Verdes":"19",
      "Peninsula":"20",
      "Pico":"20",
      "Treasury":"21",
      "Management Audit":"21",
      "Highway Program":"22",
      "Planning":"23",
      "OMB":"24",
      "Legal":"24",
      "Law Library":"24",
      "Law Library":"24",
      "East Los Angeles":"25",
      "Highland":"25",
    }
    if (aroom in rooms):
        return rooms[aroom]
    else:
        return None
