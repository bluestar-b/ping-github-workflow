package main

import (
    "encoding/json"
    "io/ioutil"
    "log"
    "net/http"
    "sync"
    "time"
)

// Link represents a link to be pinged.
type Link struct {
    ID          int    `json:"id"`
    Title       string `json:"title"`
    Description string `json:"description"`
    URL         string `json:"link"`
}

// PingTime represents a single ping time and response time.
type PingTime struct {
    Time         time.Time `json:"time"`
    ResponseTime int64     `json:"responseTime"`
}

// PingData represents the data collected from pinging a link.
type PingData struct {
    ID         int         `json:"id"`
    IsUp       bool        `json:"isUp"`
    PingTimes  []PingTime  `json:"pingTimes"`
    StatusCode int         `json:"statusCode"`
    Time       time.Time   `json:"time"`
    Description string      `json:"description"`
    URL        string      `json:"url"`
}

// Config represents the configuration for the ping service.
type Config struct {
    Port     string `json:"port"`
    Address  string `json:"address"`
    Timeout  string `json:"timeout"`
    Links    []Link `json:"links"`
}

const maxPingRecords = 100

var pingData map[int]PingData
var pingDataFile = "pingdata.json"
var pingDataLock sync.Mutex

func savePingData() {
    pingDataLock.Lock()
    defer pingDataLock.Unlock()

    data, err := json.Marshal(pingData)
    if err != nil {
        log.Printf("Error marshaling ping data: %s", err)
        return
    }

    if err := ioutil.WriteFile(pingDataFile, data, 0644); err != nil {
        log.Printf("Error writing ping data to file: %s", err)
    }
}

func pingLink(link Link, timeout time.Duration) {
    client := http.Client{
        Timeout: timeout,
    }

    start := time.Now()
    resp, err := client.Get(link.URL)
    responseTime := time.Since(start).Milliseconds()

    var isUp bool
    var statusCode int

    if err != nil {
        isUp = false
        statusCode = http.StatusInternalServerError
    } else {
        isUp = true
        statusCode = resp.StatusCode
    }

    // Check if the request exceeded the timeout
    if time.Since(start) >= timeout {
        isUp = false
        statusCode = http.StatusRequestTimeout
    }

    // Check for 5xx status codes indicating that the server is down
    if statusCode >= 500 && statusCode < 600 {
        isUp = false
    }

    pingDataLock.Lock()
    defer pingDataLock.Unlock()

    if existingData, ok := pingData[link.ID]; ok {
        if len(existingData.PingTimes) >= maxPingRecords {
            existingData.PingTimes = existingData.PingTimes[1:]
        }
        existingData.PingTimes = append(existingData.PingTimes, PingTime{
            Time:         time.Now(),
            ResponseTime: responseTime,
        })
        existingData.IsUp = isUp
        existingData.StatusCode = statusCode
        existingData.Time = time.Now()
        existingData.URL = link.URL
        pingData[link.ID] = existingData
    } else {
        pingData[link.ID] = PingData{
            ID:          link.ID,
            IsUp:        isUp,
            PingTimes:   []PingTime{{Time: time.Now(), ResponseTime: responseTime}},
            StatusCode:  statusCode,
            Time:        time.Now(),
            Description: link.Description,
            URL:         link.URL,
        }
    }
}

func pingLinksOnce(links []Link, timeout time.Duration) {
    for _, link := range links {
        pingLink(link, timeout)
    }
}

func main() {
    var config Config
    if err := loadConfig("config.json", &config); err != nil {
        panic(err)
    }

    timeout, err := time.ParseDuration(config.Timeout)
    if err != nil {
        panic(err)
    }

    pingData = make(map[int]PingData)
    pingLinksOnce(config.Links, timeout)

    savePingData()
}

