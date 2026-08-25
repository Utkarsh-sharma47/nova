import { apiRequest } from './client'
import type { ShipmentDetail } from './types'

export function getShipment(shipmentId: string): Promise<ShipmentDetail> {
  return apiRequest<ShipmentDetail>(`/v1/shipments/${shipmentId}`)
}
