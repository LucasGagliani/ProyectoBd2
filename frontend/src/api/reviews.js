import api from './client'

export const createReview = (data) => api.post('/reviews', data)
export const getReviewsByTrip = (tripId) => api.get(`/reviews/trip/${tripId}`)
export const getTripReviewStatus = (tripId) => api.get(`/reviews/trip/${tripId}/status`)
