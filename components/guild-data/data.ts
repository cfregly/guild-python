/* Copyright 2016-2017 TensorHub, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

namespace GuildData {

    const waiting = {};

    export function fetch(url, callback) {
        if (url in waiting) {
            waiting[url].push(callback);
        } else {
            waiting[url] = [callback];
            ajax(encodeDataUrl(url), fetchHandler(url));
        }
    }

    function ajax(url, callback) {
        var xhr = new XMLHttpRequest();
        xhr.open('GET', url);
        xhr.onload = function() {
            if (xhr.status === 200) {
                var json = JSON.parse(xhr.responseText);
                callback(json);
            } else {
                console.error(xhr);
                // Weak interface, but keeping it simple for
                // now. Errors are reported implicitly as null value
                // to the callback.
                callback(null);
            }
        };
        xhr.send();
    }

    function fetchHandler(url) {
        return function(data) {
            waiting[url].map(function(callback) {
                callback(data);
            });
            delete waiting[url];
        };
    }

    function encodeDataUrl(url) {
        return url.replace("/./", "/.{1}/").replace("/../", "/.{2}/");
    }

    export function scheduleFetch(url, callback, when) {
        var scheduledFetch = function() {
            fetch(url, callback);
        };
        return window.setTimeout(scheduledFetch, when);
    }
}
