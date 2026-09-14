export interface SensorDto {
  id: string;
  device_type: string;
  display_name: string;
  default_config: Record<string, unknown>;
}

export interface CreateSensorRequest {
  type: string;
  display_name: string | null;
}

export async function getSensors(): Promise<SensorDto[]> {
  const response = await fetch("http://localhost:8000/api/sensors");

  if (!response.ok) {
    throw new Error("Failed to load sensors");
  }

  return response.json();
}

export async function createSensor(
  request: CreateSensorRequest,
): Promise<SensorDto> {
  const response = await fetch("http://localhost:8000/api/sensors", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error("Failed to create sensor");
  }

  return response.json();
}
