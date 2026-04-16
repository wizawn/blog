export default {
  async fetch(request: Request, env: any, ctx: any): Promise<Response> {
    return env.__STATIC_CONTENT.fetch(request);
  }
};
