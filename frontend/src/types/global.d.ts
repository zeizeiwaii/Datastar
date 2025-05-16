declare global {
    interface Window {
        AMap: {
            Map: new (container: string | HTMLElement, options?: any) => any;
            Marker: new (options?: any) => any;
            Icon: new (options?: any) => any;
            Size: new (width: number, height: number) => any;
            PlaceSearch: new (options?: any) => any;
            Geocoder: new (options?: any) => any;
            LngLat: new (lng: number, lat: number) => any;
            Driving: new (options?: any) => any;
            Geolocation: new (options?: {
                enableHighAccuracy?: boolean;
                timeout?: number;
                maximumAge?: number;
                convert?: boolean;
                showButton?: boolean;
                buttonPosition?: string;
                buttonOffset?: any;
                zoomToAccuracy?: boolean;
            }) => any;
            Pixel: new (x: number, y: number) => any;
            DrivingPolicy?: {
                LEAST_TIME: number;
                LEAST_DISTANCE: number;
                LEAST_FEE: number;
                REAL_TRAFFIC: number;
            };
        };
        AMapLoader?: {
            load: (options: {
                key: string;
                version: string;
                plugins?: string[];
            }) => Promise<any>;
        };
    }
}

export { };

// 声明全局类型
interface Window {
    AMap: any;
    AMapLoader?: any;
}

// 扩展Vue的全局属性
declare module 'vue' {
    interface ComponentCustomProperties {
        $config: {
            apiUrl: string;
        };
    }
}

// 环境变量类型声明
interface ImportMetaEnv {
    VITE_APP_TITLE: string;
    VITE_API_BASE_URL: string;
    VITE_AMAP_KEY: string;
    [key: string]: string;
}

interface ImportMeta {
    readonly env: ImportMetaEnv;
} 