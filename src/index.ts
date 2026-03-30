export default {
  async fetch(request, env, ctx): Promise<Response> {
    const url = new URL(request.url);
    
    // 根路径重定向到 index.html
    if (url.pathname === '/') {
      return env.__STATIC_CONTENT.get('index.html', {
        cacheControl: {
          edgeTtl: 86400,
          browserTtl: 86400
        }
      });
    }
    
    // 其他路径直接返回静态内容
    return env.__STATIC_CONTENT.fetch(request);
  },
};
