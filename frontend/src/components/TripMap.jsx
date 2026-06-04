import { useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

// Fix default marker icons (Leaflet + Vite issue)
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

const ICON_ORIGIN = L.divIcon({
  className: '',
  html: `<div style="
    width:14px;height:14px;border-radius:50%;
    background:#16a34a;border:3px solid white;
    box-shadow:0 2px 6px rgba(0,0,0,0.4)">
  </div>`,
  iconAnchor: [7, 7],
})

const ICON_DEST = L.divIcon({
  className: '',
  html: `<div style="
    width:14px;height:14px;border-radius:50%;
    background:#dc2626;border:3px solid white;
    box-shadow:0 2px 6px rgba(0,0,0,0.4)">
  </div>`,
  iconAnchor: [7, 7],
})

export default function TripMap({ origin, destination = null, className = '' }) {
  const containerRef = useRef(null)
  const mapRef = useRef(null)

  useEffect(() => {
    if (!containerRef.current || !origin) return

    if (mapRef.current) {
      mapRef.current.remove()
      mapRef.current = null
    }

    const map = L.map(containerRef.current, { zoomControl: true })
    mapRef.current = map

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
      maxZoom: 19,
    }).addTo(map)

    const oLat = parseFloat(origin.lat)
    const oLon = parseFloat(origin.lon)

    // Marcador de origen siempre
    L.marker([oLat, oLon], { icon: ICON_ORIGIN })
      .addTo(map)
      .bindPopup(origin.label || '<b>Ubicación</b>')

    // Modo punto único: sin destino
    if (!destination) {
      map.setView([oLat, oLon], 15)
      return () => { map.remove(); mapRef.current = null }
    }

    const dLat = parseFloat(destination.lat)
    const dLon = parseFloat(destination.lon)

    L.marker([dLat, dLon], { icon: ICON_DEST })
      .addTo(map)
      .bindPopup(destination.label || '<b>Destino</b>')

    // Ruta via OSRM (gratuito, sin API key)
    const osrmUrl =
      `https://router.project-osrm.org/route/v1/driving/` +
      `${oLon},${oLat};${dLon},${dLat}?overview=full&geometries=geojson`

    fetch(osrmUrl)
      .then(r => r.json())
      .then(data => {
        if (data.routes && data.routes.length > 0) {
          const routeLayer = L.geoJSON(data.routes[0].geometry, {
            style: { color: '#000000', weight: 4, opacity: 0.8 },
          }).addTo(map)
          map.fitBounds(routeLayer.getBounds(), { padding: [40, 40] })
        } else {
          map.fitBounds(L.latLngBounds([[oLat, oLon], [dLat, dLon]]), { padding: [50, 50] })
        }
      })
      .catch(() => {
        L.polyline([[oLat, oLon], [dLat, dLon]], {
          color: '#000000', weight: 3, dashArray: '8, 8',
        }).addTo(map)
        map.fitBounds(L.latLngBounds([[oLat, oLon], [dLat, dLon]]), { padding: [50, 50] })
      })

    return () => {
      map.remove()
      mapRef.current = null
    }
  }, [origin?.lat, origin?.lon, destination?.lat, destination?.lon])

  return (
    <div
      ref={containerRef}
      className={`rounded-xl overflow-hidden border ${className}`}
      style={{ minHeight: '280px' }}
    />
  )
}
