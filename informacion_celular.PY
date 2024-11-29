import phonenumbers
from phonenumbers import carrier
from phonenumbers import geocoder
import opencage
from opencage.geocoder import OpenCageGeocode
import folium

# Solicita al usuario que ingrese el número de teléfono
number = input("Ingrese el número de teléfono: ")  # Ingreso por terminal
pepnumber = phonenumbers.parse(number)

# Obtén la ubicación y el proveedor de servicio
location = geocoder.country_name_for_number(pepnumber, 'en')
print("========================================") 
print("Número procesado:", number)
print("Ubicación generada:", location)

# Obtener el proveedor de servicio
serviceprovider = carrier.name_for_number(pepnumber, 'en')
if serviceprovider:
    print("Proveedor de servicio:", serviceprovider)
else:
    print("Proveedor de servicio: No se encontró información disponible")

# Reemplaza con tu clave de API
key = '944709d076f94d72977655a555f0a479'
geocoder = OpenCageGeocode(key)
query = str(location)

# Realiza la búsqueda de geocodificación
results = geocoder.geocode(query)

# Comprueba si se encontraron resultados
if results:
    lat = results[0]['geometry']['lat']
    lng = results[0]['geometry']['lng']

    print("Latitud:", lat)
    print("Longitud:", lng)
    print("========================================") 

    myMap = folium.Map(location=[lat, lng], zoom_start=9)
    folium.Marker([lat, lng], popup=location).add_to(myMap)

    myMap.save("mylocation.html")
else:
    print("No se encontraron resultados para la ubicación:", location)

input("Presione Enter para salir")