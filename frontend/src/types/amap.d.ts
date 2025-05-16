declare module '@amap/amap-jsapi-loader' {
    interface LoaderOptions {
        key: string;
        version: string;
        plugins?: string[];
    }

    interface MapOptions {
        zoom?: number;
        center?: [number, number];
    }

    interface LngLat {
        lng: number;
        lat: number;
    }

    interface MapEvent {
        lnglat: LngLat;
    }

    interface Map {
        clearMap(): void;
        add(overlay: any): void;
        setFitView(overlay?: any[]): void;
        setCenter(position: [number, number]): void;
        on(event: string, callback: (e: MapEvent) => void): void;
    }

    interface PlaceSearchOptions {
        city?: string;
        pageSize?: number;
        pageIndex?: number;
    }

    interface PlaceSearch {
        search(keyword: string, callback: (status: string, result: any) => void): void;
    }

    interface Geocoder {
        getAddress(lnglat: [number, number], callback: (status: string, result: any) => void): void;
    }

    interface MarkerOptions {
        position: [number, number];
        title?: string;
    }

    interface Marker {
        new(options: MarkerOptions): any;
    }

    interface AMap {
        Map: new (container: string | HTMLElement, options?: any) => any;
        PlaceSearch: new (options?: any) => any;
        Geocoder: new (options?: any) => any;
        Marker: new (options?: any) => any;
    }

    const AMapLoader: {
        load: (options: LoaderOptions) => Promise<AMap>;
    };

    export default AMapLoader;
}

declare global {
    interface Window {
        AMap: typeof AMap;
    }
}

declare namespace AMap {
    interface MapOptions {
        zoom?: number;
        center?: [number, number];
        viewMode?: string;
    }

    interface MarkerOptions {
        position?: [number, number];
        icon?: string;
        offset?: Pixel;
        draggable?: boolean;
        title?: string;
    }

    interface PolylineOptions {
        path?: [number, number][];
        strokeColor?: string;
        strokeWeight?: number;
    }

    interface GeolocationOptions {
        enableHighAccuracy?: boolean;
        timeout?: number;
        zoomToAccuracy?: boolean;
    }

    interface PlaceSearchOptions {
        city?: string;
        citylimit?: boolean;
        pageSize?: number;
        pageIndex?: number;
        extensions?: 'base' | 'all';
        type?: string;
        datatype?: 'poi' | 'bus' | 'busline';
        children?: number;
        offset?: number;
        radius?: number;
        lang?: 'zh_cn' | 'en';
    }

    interface Regeocode {
        formattedAddress: string;
        addressComponent: {
            province: string;
            city: string;
            district: string;
            township: string;
            street: string;
            streetNumber: string;
        };
    }

    interface GeocodeResult {
        regeocode: Regeocode;
        info: string;
    }

    interface PoiList {
        pois: Poi[];
    }

    interface Poi {
        id: string;
        name: string;
        address: string;
        location: {
            lng: number;
            lat: number;
        };
        type: string;
        distance: number;
    }

    interface SearchResult {
        info: string;
        infocode: string;
        status: string;
        count: string;
        suggestion: {
            keywords: string[];
            cities: Array<{
                name: string;
                num: number;
                citycode: string;
                adcode: string;
            }>;
        };
        pois: Array<{
            id: string;
            name: string;
            type: string;
            address: string;
            location: string;
            tel: string;
            website: string;
            email: string;
            pcode: string;
            citycode: string;
            adcode: string;
            postcode: string;
            business_area: string;
            distance: string;
            navi_poiid: string;
            entr_location: string;
            exit_location: string;
            match: string;
            recommend: string;
            indoor_map: string;
            gridcode: string;
            navi_poiid: string;
            parking_type: string;
            alias: string[];
            tag: string[];
            parent_poi: {
                id: string;
                name: string;
                type: string;
                address: string;
                location: string;
                tel: string;
                website: string;
                email: string;
                pcode: string;
                citycode: string;
                adcode: string;
                postcode: string;
                business_area: string;
                distance: string;
                navi_poiid: string;
                entr_location: string;
                exit_location: string;
                match: string;
                recommend: string;
                indoor_map: string;
                gridcode: string;
                navi_poiid: string;
                parking_type: string;
                alias: string[];
                tag: string[];
            };
            child_pois: Array<{
                id: string;
                name: string;
                type: string;
                address: string;
                location: string;
                tel: string;
                website: string;
                email: string;
                pcode: string;
                citycode: string;
                adcode: string;
                postcode: string;
                business_area: string;
                distance: string;
                navi_poiid: string;
                entr_location: string;
                exit_location: string;
                match: string;
                recommend: string;
                indoor_map: string;
                gridcode: string;
                navi_poiid: string;
                parking_type: string;
                alias: string[];
                tag: string[];
            }>;
            photos: Array<{
                title: string;
                url: string;
            }>;
        }>;
    }

    class Map {
        constructor(container: string | HTMLElement, options?: MapOptions);
        clearMap(): void;
        add(overlay: any): void;
        setFitView(overlays?: any[]): void;
        setCenter(position: [number, number]): void;
        setZoom(level: number): void;
        setBounds(bounds: any): void;
        on(event: string, handler: Function): void;
        off(event: string, handler: Function): void;
        destroy(): void;
    }

    class Marker {
        constructor(options: any);
        setMap(map: Map | null): void;
        getPosition(): any;
        on(event: string, handler: Function): void;
    }

    class Polyline {
        constructor(options: any);
        setMap(map: Map | null): void;
    }

    class InfoWindow {
        constructor(options: any);
        open(map: Map, position: any): void;
        close(): void;
    }

    class Pixel {
        constructor(x: number, y: number);
    }

    class Bounds {
        constructor(southWest: [number, number], northEast: [number, number]);
        contains(point: [number, number]): boolean;
        extend(point: [number, number]): void;
        isEmpty(): boolean;
    }

    class Geolocation {
        constructor(options?: GeolocationOptions);
        getCurrentPosition(callback: (status: string, result: any) => void): void;
    }

    class PlaceSearch {
        constructor(options?: PlaceSearchOptions);
        search(keyword: string, callback: (status: string, result: SearchResult) => void): void;
        searchNearBy(keyword: string, location: [number, number], radius: number, callback: (status: string, result: SearchResult) => void): void;
    }

    class Geocoder {
        constructor();
        getAddress(lnglat: [number, number], callback: (status: string, result: GeocodeResult) => void): void;
    }

    class Icon {
        constructor(options: any);
    }

    interface IconOptions {
        size: Size;
        image: string;
        imageSize: Size;
    }

    class Size {
        constructor(width: number, height: number);
    }
}

export { }; 