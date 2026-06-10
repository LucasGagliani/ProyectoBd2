import { useEffect, useRef, useState } from 'react'
import { updateLocation } from '../api/locations'

/**
 * Hook personalizado para rastrear ubicación GPS en tiempo real
 * y enviar updates periódicamente al backend
 */
export const useGPS = (tripId, enabled = false) => {
  const [position, setPosition] = useState(null)
  const [error, setError] = useState(null)
  const [accuracy, setAccuracy] = useState(null)
  const watchIdRef = useRef(null)
  const updateIntervalRef = useRef(null)
  const latestCoordsRef = useRef(null)

  useEffect(() => {
    if (!enabled || !tripId) {
      setError(null)
      setPosition(null)
      setAccuracy(null)
      return
    }

    // Verificar que el navegador soporta geolocalización
    if (!navigator.geolocation) {
      setError('Geolocalización no disponible en este navegador')
      return
    }

    // Comenzar a rastrear posición con alta precisión
    watchIdRef.current = navigator.geolocation.watchPosition(
      (pos) => {
        const { latitude, longitude, accuracy: acc } = pos.coords
        latestCoordsRef.current = { latitude, longitude }
        setPosition({ latitude, longitude })
        setAccuracy(acc)
        setError(null)

        // Enviar primer update inmediatamente
        sendLocationUpdate(latitude, longitude, tripId)

        // Enviar update al backend cada 10 segundos
        if (!updateIntervalRef.current) {
          updateIntervalRef.current = setInterval(() => {
            const latest = latestCoordsRef.current
            if (latest) {
              sendLocationUpdate(latest.latitude, latest.longitude, tripId)
            }
          }, 10000)
        }
      },
      (err) => {
        setError(formatGeolocationError(err))
        console.error('GPS Error:', err)
      },
      {
        enableHighAccuracy: true,
        maximumAge: 0,
        timeout: 5000,
      }
    )

    return () => {
      if (watchIdRef.current) {
        navigator.geolocation.clearWatch(watchIdRef.current)
        watchIdRef.current = null
      }
      if (updateIntervalRef.current) {
        clearInterval(updateIntervalRef.current)
        updateIntervalRef.current = null
      }
      latestCoordsRef.current = null
    }
  }, [tripId, enabled])

  return { position, error, accuracy }
}

function formatGeolocationError(err) {
  switch (err.code) {
    case err.PERMISSION_DENIED:
      return 'Acceso a ubicación denegado. Habilitá la ubicación del navegador para registrar el recorrido.'
    case err.POSITION_UNAVAILABLE:
      return 'No se pudo obtener tu ubicación actual.'
    case err.TIMEOUT:
      return 'Se agotó el tiempo para obtener la ubicación.'
    default:
      return `Error de GPS: ${err.message}`
  }
}

/**
 * Envía actualización de ubicación al backend
 */
async function sendLocationUpdate(latitude, longitude, tripId) {
  try {
    await updateLocation({
      id_viaje: tripId,
      latitud: latitude,
      longitud: longitude,
    })
  } catch (err) {
    console.error('Error enviando ubicación:', err)
  }
}
