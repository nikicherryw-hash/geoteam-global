import unittest
from unittest.mock import patch
import httpx
from .ai_search import _source_page_image, MAX_SOURCE_BYTES


class SourceFetchTests(unittest.IsolatedAsyncioTestCase):
    async def fetch(self, handler):
        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        with patch('sourcing.search_v2.ai_search.httpx.AsyncClient', return_value=client), patch('sourcing.search_v2.ai_search._public_page_url', return_value=True):
            return await _source_page_image('https://seller.example/912', {'model':'ROTAX 912'})

    async def test_exact_photo_from_bounded_html(self):
        image = await self.fetch(lambda req: httpx.Response(200, headers={'Content-Type':'text/html'}, text='<img src="/912.jpg" alt="Rotax aircraft engine 912">'))
        self.assertEqual(image, 'https://seller.example/912.jpg')

    async def test_oversized_and_malformed_length(self):
        for length in (str(MAX_SOURCE_BYTES + 1), 'invalid'):
            with self.subTest(length=length):
                self.assertIsNone(await self.fetch(lambda req: httpx.Response(200, headers={'Content-Type':'text/html','Content-Length':length}, content=b'x')))

    async def test_chunked_decoded_byte_limit(self):
        class Chunks(httpx.AsyncByteStream):
            count = 0
            async def __aiter__(self):
                for _ in range(20):
                    self.count += 1
                    yield b'x' * 100000
        stream = Chunks()
        self.assertIsNone(await self.fetch(lambda req: httpx.Response(200, headers={'Content-Type':'text/html'}, stream=stream)))
        self.assertEqual(stream.count, 6)

    async def test_redirect_loop_is_bounded(self):
        calls = []
        def handler(req):
            calls.append(req.url)
            return httpx.Response(302, headers={'location':'/again'})
        self.assertIsNone(await self.fetch(handler))
        self.assertEqual(len(calls), 2)
