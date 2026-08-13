from __future__ import annotations

import math
from typing import Any

import httpx

from config_loader import Settings


class AmapError(RuntimeError):
    pass


class AmapClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def nearby_funeral_homes(
        self, longitude: float, latitude: float, city: str, limit: int = 8
    ) -> list[dict[str, Any]]:
        if not self.settings.amap_ready:
            raise AmapError("高德地图密钥未配置")

        params = {
            "key": self.settings.amap_api_key,
            "location": f"{longitude:.6f},{latitude:.6f}",
            "keywords": "殡仪馆",
            "radius": 50000,
            "sortrule": "distance",
            "offset": 20,
            "page": 1,
            "extensions": "all",
        }
        data = await self._get("/v3/place/around", params)
        pois = data.get("pois") or []

        candidates = [self._normalize_poi(poi, longitude, latitude) for poi in pois]
        candidates = [item for item in candidates if self._looks_like_funeral_home(item)]

        if len(candidates) < 3:
            text_data = await self._get(
                "/v3/place/text",
                {
                    "key": self.settings.amap_api_key,
                    "keywords": "殡仪馆",
                    "city": city,
                    "citylimit": "true",
                    "offset": 20,
                    "page": 1,
                    "extensions": "all",
                },
            )
            known_ids = {item["id"] for item in candidates}
            for poi in text_data.get("pois") or []:
                item = self._normalize_poi(poi, longitude, latitude)
                if item["id"] not in known_ids and self._looks_like_funeral_home(item):
                    candidates.append(item)
                    known_ids.add(item["id"])

        candidates.sort(key=lambda item: item["distance_m"])
        return candidates[:limit]

    async def geocode(self, address: str, city: str) -> dict[str, Any]:
        if not self.settings.amap_ready:
            raise AmapError("高德地图密钥未配置")
        data = await self._get(
            "/v3/geocode/geo",
            {
                "key": self.settings.amap_api_key,
                "address": address,
                "city": city,
            },
        )
        geocodes = data.get("geocodes") or []
        if not geocodes:
            raise AmapError("没有找到这个地点")
        item = geocodes[0]
        try:
            longitude, latitude = [float(value) for value in item["location"].split(",")]
        except (KeyError, ValueError) as exc:
            raise AmapError("地点坐标无法解析") from exc
        return {
            "longitude": longitude,
            "latitude": latitude,
            "formatted_address": str(item.get("formatted_address") or address),
            "city": self._scalar_text(item.get("city"))
            or self._scalar_text(item.get("province"))
            or city,
            "level": str(item.get("level") or ""),
        }

    async def normalize_gps_location(
        self, longitude: float, latitude: float
    ) -> dict[str, Any]:
        """Convert browser WGS-84 coordinates to Amap coordinates and identify the city."""
        if not self.settings.amap_ready:
            raise AmapError("高德地图密钥未配置")
        converted = await self._get(
            "/v3/assistant/coordinate/convert",
            {
                "key": self.settings.amap_api_key,
                "locations": f"{longitude:.6f},{latitude:.6f}",
                "coordsys": "gps",
            },
        )
        raw_location = str(converted.get("locations") or "")
        try:
            amap_lng, amap_lat = [float(value) for value in raw_location.split(",")]
        except (ValueError, TypeError) as exc:
            raise AmapError("定位坐标转换失败") from exc

        reverse = await self._get(
            "/v3/geocode/regeo",
            {
                "key": self.settings.amap_api_key,
                "location": f"{amap_lng:.6f},{amap_lat:.6f}",
                "extensions": "base",
            },
        )
        regeocode = reverse.get("regeocode") or {}
        component = regeocode.get("addressComponent") or {}
        province = self._scalar_text(component.get("province"))
        city = self._scalar_text(component.get("city")) or province
        return {
            "longitude": amap_lng,
            "latitude": amap_lat,
            "formatted_address": self._scalar_text(
                regeocode.get("formatted_address")
            )
            or "当前位置",
            "city": city,
            "district": self._scalar_text(component.get("district")),
            "coordinate_system": "GCJ-02",
        }

    async def static_map(
        self,
        longitude: float,
        latitude: float,
        markers: list[tuple[float, float, str]],
    ) -> tuple[bytes, str]:
        if not self.settings.amap_ready:
            raise AmapError("高德地图密钥未配置")
        marker_value = "|".join(
            f"mid,,{label}:{lng:.6f},{lat:.6f}" for lng, lat, label in markers[:5]
        )
        params = {
            "key": self.settings.amap_api_key,
            "location": f"{longitude:.6f},{latitude:.6f}",
            "zoom": 10,
            "size": "750*360",
            "scale": 2,
            "markers": marker_value,
        }
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            response = await client.get(
                f"{self.settings.amap_endpoint}/v3/staticmap", params=params
            )
            response.raise_for_status()
            content_type = response.headers.get("content-type", "image/png")
            if not content_type.startswith("image/"):
                raise AmapError("高德静态地图返回了非图片内容")
            return response.content, content_type

    async def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(f"{self.settings.amap_endpoint}{path}", params=params)
            response.raise_for_status()
            data = response.json()
        if data.get("status") != "1":
            raise AmapError(data.get("info") or "高德地图查询失败")
        return data

    @staticmethod
    def _looks_like_funeral_home(item: dict[str, Any]) -> bool:
        name = item["name"]
        poi_type = item.get("type", "")
        excluded = (
            "公墓",
            "陵园",
            "寿衣",
            "殡葬用品",
            "殡葬服务中心",
            "服务站",
            "服务部",
            "告别厅",
            "厅",
        )
        # A keyword match alone also returns halls, shops and private service desks.
        # The final Amap category must explicitly identify a funeral home.
        return (
            "殡仪馆" in name
            and name.strip() != "殡仪馆"
            and poi_type.endswith("殡仪馆")
            and not any(word in name for word in excluded)
        )

    @classmethod
    def _normalize_poi(
        cls, poi: dict[str, Any], origin_lng: float, origin_lat: float
    ) -> dict[str, Any]:
        location = str(poi.get("location") or "0,0").split(",")
        try:
            lng, lat = float(location[0]), float(location[1])
        except (ValueError, IndexError):
            lng, lat = 0.0, 0.0
        raw_distance = poi.get("distance")
        try:
            distance_m = int(float(raw_distance))
        except (TypeError, ValueError):
            distance_m = int(cls._haversine(origin_lng, origin_lat, lng, lat))
        address = poi.get("address")
        if isinstance(address, list):
            address = "".join(str(part) for part in address)
        tel = poi.get("tel")
        if isinstance(tel, list):
            tel = " / ".join(str(item) for item in tel)
        return {
            "id": str(poi.get("id") or f"{lng},{lat}"),
            "name": str(poi.get("name") or "未命名机构"),
            "address": str(address or "地址待确认"),
            "longitude": lng,
            "latitude": lat,
            "distance_m": distance_m,
            "phone": str(tel or ""),
            "type": str(poi.get("type") or ""),
            "source": "amap",
        }

    @staticmethod
    def _haversine(lng1: float, lat1: float, lng2: float, lat2: float) -> float:
        if not lng2 or not lat2:
            return 99_999_999
        radius = 6_371_000
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        d_phi = math.radians(lat2 - lat1)
        d_lambda = math.radians(lng2 - lng1)
        a = (
            math.sin(d_phi / 2) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
        )
        return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    @staticmethod
    def _scalar_text(value: Any) -> str:
        return str(value).strip() if isinstance(value, (str, int, float)) else ""
