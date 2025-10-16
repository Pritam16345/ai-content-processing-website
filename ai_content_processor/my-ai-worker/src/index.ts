// src/index.ts (Simplified JavaScript Version)

export default {
  async fetch(request, env) {
    if (request.method !== 'POST') {
      return new Response('Expected POST request', { status: 405 });
    }

    try {
      const { prompt } = await request.json();

      if (!prompt) {
        return new Response('Missing "prompt" in request body', { status: 400 });
      }

      const messages = [{ role: 'user', content: prompt }];

      const aiResponse = await env.AI.run('@cf/meta/llama-3-8b-instruct', { messages });

      return new Response(JSON.stringify(aiResponse), {
        headers: { 'Content-Type': 'application/json' },
      });
    } catch (e) {
      console.error(e);
      // Return the actual error message for better debugging
      return new Response(e.message, { status: 500 });
    }
  },
};