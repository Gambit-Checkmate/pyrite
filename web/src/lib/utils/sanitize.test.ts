import { describe, expect, it } from 'vitest';
import { marked } from 'marked';
import { jsonForScriptTag, sanitizeHtml } from './sanitize';

const render = (md: string) => sanitizeHtml(marked.parse(md, { async: false }) as string);

describe('sanitizeHtml', () => {
	it('strips script tags that markdown passes through verbatim', () => {
		expect(render('hello <script>alert(1)</script>')).not.toContain('<script');
	});

	it('strips inline event handlers', () => {
		const html = render('<img src=x onerror="alert(1)">');
		expect(html).not.toContain('onerror');
	});

	it('strips javascript: URLs from markdown links', () => {
		expect(render('[click](javascript:alert(1))')).not.toContain('javascript:');
	});

	it('strips iframes and embedded objects', () => {
		const html = render('<iframe src="https://evil.example"></iframe><object data="x"></object>');
		expect(html).not.toContain('<iframe');
		expect(html).not.toContain('<object');
	});

	it('keeps the markup the entry renderer depends on', () => {
		const html = sanitizeHtml(
			'<h2 id="my-heading">T</h2><p id="block-abc">x</p>' +
				'<a href="/entries/foo" class="wikilink" data-wikilink="foo">foo</a>' +
				'<div class="callout callout-info">c</div><pre><code class="language-py">x</code></pre>'
		);
		expect(html).toContain('id="my-heading"');
		expect(html).toContain('id="block-abc"');
		expect(html).toContain('href="/entries/foo"');
		expect(html).toContain('class="wikilink"');
		expect(html).toContain('callout-info');
		expect(html).toContain('language-py');
	});
});

describe('jsonForScriptTag', () => {
	it('cannot be broken out of with a closing script tag', () => {
		const out = jsonForScriptTag({ name: '</script><script>alert(1)</script>' });
		expect(out).not.toContain('</script');
		expect(JSON.parse(out).name).toBe('</script><script>alert(1)</script>');
	});
});
