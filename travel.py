import json
import math
import urllib.parse


import matplotlib
import requests
from flask import Flask, render_template, request, send_from_directory, url_for
import matplotlib.pyplot as plt
matplotlib.use('TkAgg')
import numpy as np
import random
from math import radians, cos


app = Flask(__name__)

@app.route('/apple.jpg')
def apple():
    return send_from_directory('templates', 'apple.jpg')

@app.route('/style.css')
def style():
    return send_from_directory('templates', 'style.css')


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET" and "submit" in request.args:

        # openweathermap api key
        api_key = "PUT_YOUR_API_KEY_HERE"

        days = request.args.get("days")
        starting_point = request.args.get("start")
        destination = request.args.get("destination")

        cities = [starting_point, destination]
        coordinates = []

        for i in range(0, len(cities)):
            city_encoded = cities[i]
            url = f"https://nominatim.openstreetmap.org/search.php?q={city_encoded}&limit=1&format=jsonv2"
            response = requests.get(url)
            data = response.json()

            lat = data[0]['lat']
            lng = data[0]["lon"]
            temp = [lat, lng]

            coordinates.append(temp)

        ##print("Koordinati:", coordinates)

        start_point = (coordinates[0][0], coordinates[0][1])
        end_point = (coordinates[1][0], coordinates[1][1])
        n = int(days)



        # računamo zračno razdaljo med dvema mestoma v km
        def haversine(lat1, lon1, lat2, lon2):
            # convert decimal degrees to radians
            lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

            # haversine formula
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
            c = 2 * math.asin(math.sqrt(a))

            # earth's radius in km
            radius = 6371

            return radius * c

        # računamo dinamično velikost radija glede na število dni potovanja in zračno razdaljo
        def calculate_radius_size(air_distance, num_days):
            average_distance_per_day = air_distance / num_days
            default_radius_size = average_distance_per_day / 2

            if num_days <= 2:
                radius_size = default_radius_size * 1.5
            elif num_days <= 4:
                radius_size = default_radius_size * 1.2
            elif num_days <= 6:
                radius_size = default_radius_size * 1.1
            elif num_days <= 8:
                radius_size = default_radius_size * 1.05
            elif num_days <= 10:
                radius_size = default_radius_size * 1.02
            else:
                radius_size = default_radius_size

            return radius_size

        # z linearno funkcijo kreiramo točke na poti med dvema mestoma (linearno funkcijo razdelimo na n delov, potem pa v točkah na tej funkciji v dinamičnem radiusu izberemo točko)
        def create_points2(start_point, end_point, n, air_distance, radius_size):
            x1, y1 = float(start_point[0]), float(start_point[1])
            x2, y2 = float(end_point[0]), float(end_point[1])
            points2 = []
            dx = (x2 - x1) / n
            dy = (y2 - y1) / n
            ##print("Air distance:", air_distance, "km")
            ##print("Radius size:", radius_size)
            for i in range(n + 1):
                x = x1 + i * dx
                y = y1 + i * dy
                new_x = x + random.uniform(-radius_size / 111.12, radius_size / 111.12)
                new_y = y + random.uniform(-radius_size / 111.12, radius_size / 111.12)
                points2.append([new_x, new_y])
            return points2


        air_distance = haversine(float(coordinates[0][0]), float(coordinates[0][1]), float(coordinates[1][0]), float(coordinates[1][1]))
        radius_size = calculate_radius_size(air_distance, n)
        points2 = create_points2(start_point, end_point, n, air_distance, radius_size)

        # izrisemo točke na poti med dvema mestoma (to je samo za vizualizacijo, v produkciji se to ne izvaja)
        def plot_linear_function(start_point, end_point, points2):
            points2 = points2[1:-1]

            x2 = [start_point[0]] + [p[0] for p in points2] + [end_point[0]]
            y2 = [start_point[1]] + [p[1] for p in points2] + [end_point[1]]

            plt.plot(x2, y2, 'bo', markersize=15)
            plt.plot(x2, y2, 'k', linewidth=3)
            plt.show()
        #plot_linear_function(start_point, end_point, points2)


        points2 = points2[1:-1] # odstranimo prvo in zadnjo točko, ker so to začetna in končna točka ki so dejansko randomizirani z dinamičnik radiusom
        points2.insert(0, coordinates[0]) # dodamo pravo začetno točko
        points2.insert(len(points2), coordinates[1]) # dodamo pravo končno točko
        result = []
        for inner_list in points2:
            result.append(str(inner_list))

        string = "/".join(result)
        string = string.replace("[", "")
        string = string.replace("]", "")
        string = string.replace(" ", "")
        string = string.replace("'", "")

        ##print(string)
        google_maps_url = f"https://www.google.com/maps/dir/{string}"
        ##print(google_maps_url)

        def get_closest_city_from_sea(cord1, cord2):

            lat1, lon1 = cord1[0], cord1[1]
            lat2, lon2 = cord2[0], cord2[1]

            endpoint = f"http://api.openweathermap.org/data/2.5/box/city?bbox={lon1},{lat1},{lon2},{lat2},10&appid={api_key}"
            ##print(endpoint)

            # Make the API call
            response = requests.get(endpoint)

            # Check for a successful response
            if (response.status_code == 200) and (len(response.text) > 2):
                # Parse the JSON data
                data = json.loads(response.text)

                names = []
                lat_lon = []
                for item in data['list']:
                    names.append(item['name'])
                    lat_lon.append([item['coord']['Lat'], item['coord']['Lon']])

                #print("names: ", names)
                ##print("lat_lon: ", lat_lon)

                # get closest city from sea
                razdalje = []
                for i in range(0, len(lat_lon)):
                    lat = lat_lon[i][0]
                    lon = lat_lon[i][1]
                    distance = haversine(lat1, lon1, lat, lon)
                    razdalje.append(distance)
                min_index = razdalje.index(min(razdalje))
                mesta2.append(names[min_index])
                mesta2_lat_lon.append(lat_lon[min_index])
            else:
                print("Error: ", response.status_code, response.text)


        def get_new_coordinate(lon1, lat1, distance_in_km):
            # calculate the difference in latitude and longitude
            dlat = distance_in_km / 111.13  # 1 degree of latitude = 111.13 km
            dlon = distance_in_km / (111.13 * cos(radians(lat1)))  # 1 degree of longitude = 111.13 * cos(latitude) km

            # calculate the new coordinates
            lat2 = lat1 + dlat
            lon2 = lon1 - dlon

            return lon2, lat2


        # poiščemo ime mesta glede na koordinate
        mesta = points2[1:-1]
        mesta2 = []
        mesta2_lat_lon = []
        for i in range(0, len(mesta)):
            lat = mesta[i][0]
            long = mesta[i][1]
            url = f"https://nominatim.openstreetmap.org/reverse.php?lat={lat}&lon={long}&zoom=10&format=jsonv2"
            response = requests.get(url)

            if response.status_code == 200:
                data = response.json()
                if ("error" in data and data["error"] == "Unable to geocode") or (data["name"] == "Italia") or (data["name"] == "none"):

                    # calculate new coordinate 20km in the up-left direction
                    distance_in_km = float(radius_size)
                    lon2, lat2 = get_new_coordinate(long, lat, distance_in_km)
                    #print(f"Up-left coordinate: {lon2}, {lat2}")

                    # calculate new coordinate 20km in the down-right direction
                    distance_in_km = -float(radius_size)
                    lon3, lat3 = get_new_coordinate(long, lat, distance_in_km)
                    #print(f"Down-right coordinate: {lon3}, {lat3}")

                    cord1 = [lat2, lon2]
                    cord2 = [lat3, lon3]

                    get_closest_city_from_sea(cord1, cord2)
                else:
                    mesta2.append(data["name"])
                    mesta2_lat_lon.append([data["lat"], data["lon"]])
            else:
                print("Error: API request failed")

        #print("mesta2: ", mesta2)
        #print("mesta2_lat_lon: ", mesta2_lat_lon)

        def check_for_best_weather_in_cites_array(lat_lon, st, mesto_lat_lon, names_okoli, x):
            weather_array = []

            icon_a = []
            degres_celsuius_a = []
            wind_speed_a = []
            humidity_a = []
            sunrise_a = []

            scores = {
                "thunderstorm with light rain": 1,
                "thunderstorm with rain": 2,
                "thunderstorm with heavy rain": 3,
                "light thunderstorm": 1,
                "thunderstorm": 2,
                "heavy thunderstorm": 3,
                "ragged thunderstorm": 2,
                "thunderstorm with light drizzle": 1,
                "thunderstorm with drizzle": 2,
                "thunderstorm with heavy drizzle": 3,
                "light intensity drizzle": 1,
                "drizzle": 2,
                "heavy intensity drizzle": 3,
                "light intensity drizzle rain": 1,
                "drizzle rain": 2,
                "heavy intensity drizzle rain": 3,
                "shower rain and drizzle": 2,
                "heavy shower rain and drizzle": 3,
                "shower drizzle": 1,
                "light rain": 1,
                "moderate rain": 2,
                "heavy intensity rain": 3,
                "very heavy rain": 4,
                "extreme rain": 5,
                "freezing rain": 3,
                "light intensity shower rain": 1,
                "shower rain": 2,
                "heavy intensity shower rain": 3,
                "ragged shower rain": 2,
                "light snow": 2,
                "snow": 3,
                "heavy snow": 4,
                "sleet": 3,
                "light shower sleet": 2,
                "shower sleet": 3,
                "light rain and snow": 2,
                "rain and snow": 3,
                "light shower snow": 2,
                "shower snow": 3,
                "heavy shower snow": 4,
                "mist": 1,
                "smoke": 1,
                "haze": 1,
                "sand/dust whirls": 1,
                "fog": 1,
                "sand": 1,
                "dust": 1,
                "volcanic ash": 1,
                "squalls": 1,
                "tornado": 1,
                "clear sky": 5,
                "sky is clear": 5,
                "few clouds": 3,
                "scattered clouds": 3,
                "broken clouds": 2,
                "overcast clouds": 1
            }

            if (len(lat_lon) < 5):
                n = len(lat_lon)
            else:
                n = 5

            if (len(lat_lon) == 0):
                lat_lon = mesto_lat_lon
                n = 1



            #print("n", n)

            for i in range(0, n):
                #print("i1", i)
                lat = lat_lon[i][0]
                lon = lat_lon[i][1]
                cnt = x

                url = f"https://pro.openweathermap.org/data/2.5/forecast/climate?lat={lat}&lon={lon}&cnt={cnt}&appid={api_key}&units=metric"
                #print("url: ", url)
                response = requests.get(url)

                best_weather = None
                best_score = 0
                y = -1
                weather_data = "no_data.png"
                if response.status_code == 200:
                    data = response.json()
                    #print("st: ", st)
                    weather = data["list"][st]["weather"][0]["description"]
                    icon = data["list"][st]["weather"][0]["icon"]
                    degres_celsuius = data["list"][st]["temp"]["day"]
                    wind_speed = data["list"][st]["speed"]
                    humidity = data["list"][st]["humidity"]
                    sunrise = data["list"][st]["sunrise"]

                    weather_array.append(weather)
                    icon_a.append(icon)
                    degres_celsuius_a.append(degres_celsuius)
                    wind_speed_a.append(wind_speed)
                    humidity_a.append(humidity)
                    sunrise_a.append(sunrise)


                    for weather in weather_array:
                        if scores[weather] > best_score:
                            best_score = scores[weather]
                            best_weather = weather
                            y += 1
                            degres_celsuius = degres_celsuius_a[y]
                            wind_speed = wind_speed_a[y]
                            humidity = humidity_a[y]
                            sunrise = sunrise_a[y]
                            icon = icon_a[y]


                    #print("weather_array: ", weather_array)
                    #print("icon_a: ", icon_a)
                    #print("best_day: ", best_weather)
                    #print("best_score: ", best_score)

                else:
                    best_weather = "error"
                    best_score = "error"
                    y = "error"
                    icon = "no_data.png"
                    degres_celsuius = "no_data"
                    wind_speed = "no_data"
                    humidity = "no_data"
                    sunrise = "no_data"
                    print("Error: API request failed")




            return best_weather, best_score, y, degres_celsuius, wind_speed, humidity, sunrise, icon


        def get_best_weather(mesta2, mesta2_lat_lon, radius_size):
            # get coordinates of cities
            lat_lon_mesto = mesta2_lat_lon

            for i in range(0, len(mesta2)):
                #print("za mesto v arrayu: ", i)
                #print("mesto: ", mesta2[i])

                lat = float(lat_lon_mesto[i][0])
                long = float(lat_lon_mesto[i][1])

                if (radius_size > 25):
                    radius_size = 25

                # get cities within radius_size of this coordinate
                # calculate new coordinate radius_size in the up-left direction
                distance_in_km = float(radius_size)
                lon2, lat2 = get_new_coordinate(long, lat, distance_in_km)
                #print(f"Up-left coordinate: {lon2}, {lat2}")

                # calculate new coordinate radius_size in the down-right direction
                distance_in_km = -float(radius_size)
                lon3, lat3 = get_new_coordinate(long, lat, distance_in_km)
                #print(f"Down-right coordinate: {lon3}, {lat3}")


                endpoint = f"http://api.openweathermap.org/data/2.5/box/city?bbox={lon2},{lat2},{lon3},{lat3},10&appid={api_key}"
                #print(endpoint)

                # Make the API call
                response = requests.get(endpoint)

                # Check for a successful response
                if (response.status_code == 200) and (len(response.text) > 2):
                    # Parse the JSON data
                    data = json.loads(response.text)

                    names_okoli = []
                    lat_lon = []
                    for item in data['list']:
                        names_okoli.append(item['name'])
                        lat_lon.append([item['coord']['Lat'], item['coord']['Lon']])

                    #print("mesta okoli mesta: ", names_okoli)
                    #print("lat_lon: ", lat_lon)

                    #print("i za mesto okoli mesta: ", i)
                    #print("lat_lon_og_mesto[i]: ", lat_lon_mesto[i])
                    num_of_days = days = request.args.get("days")
                    x = int(num_of_days)
                    best_weather, best_score, y, degres_celsuius, wind_speed, humidity, sunrise, icon = check_for_best_weather_in_cites_array(lat_lon, i, lat_lon_mesto[i], names_okoli, x)
                    if (best_weather == "error"):
                        mesta_po_vremenu.append([mesta2[i], "No weather data", "No weather data", degres_celsuius, wind_speed, humidity, sunrise, icon])
                    else:
                        mesta_po_vremenu.append([names_okoli[y], best_weather, best_score, degres_celsuius, wind_speed, humidity, sunrise, icon])


                else:
                    print("Error: API request failede")
                    icon = "no_data.png"
                    degres_celsuius = "no_data"
                    wind_speed = "no_data"
                    humidity = "no_data"
                    sunrise = "no_data"
                    mesta_po_vremenu.append([mesta2[i], "No weather data", "No weather data", degres_celsuius, wind_speed, humidity, sunrise, icon])


        mesta_po_vremenu = []
        get_best_weather(mesta2, mesta2_lat_lon, radius_size)
        print(mesta_po_vremenu)
        mesta_po_vremenu_json = json.dumps(mesta_po_vremenu)

        result = ""
        for city in mesta_po_vremenu:
            result += city[0] + "/"
        result = result[:-1]  # remove the last slash

        print(result)
        google_maps_url_v = f"https://www.google.com/maps/dir/{starting_point}/{result}/{destination}"
        print(google_maps_url_v)


        result = []
        for inner_list in mesta2:
            result.append(str(inner_list))

        string = "/".join(result)
        string = string.replace("[", "")
        string = string.replace("]", "")
        string = string.replace(" ", "")

        print(string)
        google_maps_url = f"https://www.google.com/maps/dir/{starting_point}/{string}/{destination}"
        print(google_maps_url)

        text = "Google Maps Link!"

        return render_template('index.html', url=google_maps_url_v, text=text, mesta_po_vremenu_json=mesta_po_vremenu_json)

    return render_template('index.html')


if __name__ == "__main__":
    app.run()
