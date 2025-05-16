/// <reference types="vite/client" />

declare module '*.vue' {
    import type { DefineComponent } from 'vue'
    const component: DefineComponent<{}, {}, any>
    export default component
}

declare namespace AMap {
    class Map {
        constructor(container: string | HTMLElement, options?: MapOptions);
        setCenter(position: [number, number]): void;
        add(marker: Marker): void;
        clearMap(): void;
        destroy(): void;
    }

    interface MapOptions {
        zoom?: number;
        center?: [number, number];
    }

    class Marker {
        constructor(options: MarkerOptions);
        setPosition(position: [number, number]): void;
        on(event: string, callback: (e: any) => void): void;
    }

    interface MarkerOptions {
        position?: [number, number];
        draggable?: boolean;
    }

    class PlaceSearch {
        constructor(options?: PlaceSearchOptions);
        search(keyword: string, callback: (status: string, result: any) => void): void;
    }

    interface PlaceSearchOptions {
        pageSize?: number;
        extensions?: string;
    }

    class Geocoder {
        constructor();
        getAddress(lnglat: [number, number], callback: (status: string, result: any) => void): void;
    }
}

declare interface Window {
    AMap: typeof AMap;
} 