export interface Location {
    lng: number;
    lat: number;
}

export interface POI {
    id: string;
    name: string;
    address?: string;
    location: Location;
    type?: string;
    typecode?: string;
    pname?: string; // 省份名称
    cityname?: string; // 城市名称
    adname?: string; // 区县名称
    original?: any; // 原始POI数据
}

export interface Request {
    id?: string;
    userId: number;
    origin: string;
    destination: string;
    departureTime: string;
    peopleCount: number;
    originLocation: Location;
    destinationLocation: Location;
    originPOI?: POI; // 保存完整的起点POI信息
    destinationPOI?: POI; // 保存完整的终点POI信息
    status?: string;
    createdAt?: string;
    updatedAt?: string;
}

export interface RequestForm {
    origin: string;
    destination: string;
    departureTime: string;
} 