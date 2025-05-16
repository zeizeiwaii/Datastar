import { ElMessage } from 'element-plus';
import amapConfig from './amapConfig';

interface MapInitOptions {
    container: HTMLElement;
    zoom?: number;
    center?: [number, number];
    plugins?: string[];
    viewMode?: '2D' | '3D';
}

export class MapInitializer {
    private static instance: MapInitializer;
    private initPromise: Promise<any> | null = null;
    private retryCount = 0;
    private readonly MAX_RETRIES = 3;
    private readonly RETRY_DELAY = 1000; // 重试延迟时间（毫秒）

    private constructor() { }

    public static getInstance(): MapInitializer {
        if (!MapInitializer.instance) {
            MapInitializer.instance = new MapInitializer();
        }
        return MapInitializer.instance;
    }

    public async initMap(options: MapInitOptions): Promise<any> {
        try {
            console.log('开始初始化地图...');
            const AMap = await this.loadAMapScript();
            const map = await this.createMapInstance(options, AMap);
            console.log('地图初始化成功');
            return map;
        } catch (error) {
            console.error('地图初始化失败:', error);
            if (this.retryCount < this.MAX_RETRIES) {
                this.retryCount++;
                console.log(`等待${this.RETRY_DELAY / 1000}秒后进行第 ${this.retryCount} 次重试...`);
                await new Promise(resolve => setTimeout(resolve, this.RETRY_DELAY));
                return this.initMap(options);
            }
            ElMessage.error('地图初始化失败，请检查网络连接后刷新页面重试');
            throw new Error('地图初始化失败，已达到最大重试次数');
        }
    }

    private async loadAMapScript(): Promise<any> {
        if (this.initPromise) {
            return this.initPromise;
        }

        this.initPromise = new Promise((resolve, reject) => {
            try {
                // 如果已经加载过AMap，直接返回
                if ((window as any).AMap) {
                    console.log('AMap已存在，直接使用');
                    resolve((window as any).AMap);
                    return;
                }

                console.log('开始加载高德地图JSAPI...');

                // 加载高德地图JSAPI
                const script = document.createElement('script');
                script.type = 'text/javascript';
                script.async = true;
                script.src = `https://webapi.amap.com/maps?v=${amapConfig.JS_API_CONFIG.VERSION}&key=${amapConfig.JS_API_KEY}&plugin=${amapConfig.JS_API_CONFIG.PLUGINS.join(',')}&callback=initAMap`;

                // 创建回调函数
                (window as any).initAMap = () => {
                    const AMap = (window as any).AMap;
                    if (!AMap) {
                        reject(new Error('AMap对象加载失败'));
                        return;
                    }

                    // 设置安全密钥
                    try {
                        AMap.SecurityConfig.securityJsCode = amapConfig.SECURITY_JSCODE;
                        console.log('安全密钥配置成功');
                    } catch (error) {
                        console.error('安全密钥配置失败:', error);
                        reject(error);
                        return;
                    }

                    console.log('高德地图API加载成功');
                    resolve(AMap);
                };

                script.onerror = (error) => {
                    console.error('高德地图API加载失败:', error);
                    reject(new Error('地图API加载失败，请检查网络连接'));
                };

                document.head.appendChild(script);
                console.log('JSAPI脚本已添加到页面');
            } catch (error) {
                console.error('加载地图脚本时发生错误:', error);
                reject(error);
            }
        });

        return this.initPromise;
    }

    private async createMapInstance(options: MapInitOptions, AMap: any): Promise<any> {
        const { container, zoom = 12, center = [amapConfig.DEFAULT_CENTER.lng, amapConfig.DEFAULT_CENTER.lat], viewMode = '2D' } = options;

        if (!container) {
            throw new Error('地图容器元素未找到');
        }

        return new Promise((resolve, reject) => {
            try {
                console.log('开始创建地图实例，参数:', {
                    container: container.id,
                    zoom,
                    center,
                    viewMode
                });

                const map = new AMap.Map(container, {
                    zoom,
                    center,
                    viewMode,
                    resizeEnable: true,
                });

                // 添加基础控件
                map.addControl(new AMap.Scale());
                map.addControl(new AMap.ToolBar({ position: 'RT' }));

                // 添加事件监听
                map.on('complete', () => {
                    console.log('地图加载完成');
                    resolve(map);
                });

                map.on('error', (error: any) => {
                    console.error('地图加载错误:', error);
                    reject(error);
                });

            } catch (error) {
                console.error('创建地图实例失败:', error);
                reject(error);
            }
        });
    }

    public clearMapInstance(map: any): void {
        if (!map) {
            console.warn('清理地图实例：map对象为空');
            return;
        }

        try {
            // 清除所有覆盖物
            map.clearMap();

            // 重置地图状态
            map.setStatus({
                dragEnable: true,
                zoomEnable: true,
                doubleClickZoom: true,
                keyboardEnable: true,
                scrollWheel: true
            });

            console.log('地图实例已清理完成');
        } catch (error) {
            console.error('清理地图实例时出错:', error);
            ElMessage.warning('清理地图时出现错误，建议刷新页面');
        }
    }
}

export default MapInitializer.getInstance(); 