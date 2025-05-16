/// <reference types="vite/client" />

interface ImportMetaEnv {
    readonly VITE_AMAP_KEY: string
    readonly VITE_AMAP_SECURITY_JS_CODE: string
    readonly VITE_API_BASE_URL: string
}

interface ImportMeta {
    readonly env: ImportMetaEnv
}

declare module '*.vue' {
    import type { DefineComponent } from 'vue'
    const component: DefineComponent<{}, {}, any>
    export default component
}

declare global {
    interface Window {
        AMap: {
            Map: new (container: string | HTMLElement, options?: any) => any;
            Marker: new (options?: any) => any;
            Icon: new (options?: any) => any;
            Size: new (width: number, height: number) => any;
            PlaceSearch: new (options?: any) => any;
            Geocoder: new (options?: any) => any;
        };
    }
} 