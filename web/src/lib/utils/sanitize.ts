/**
 * HTML sanitization for every `{@html}` sink that renders KB content.
 *
 * `marked` passes raw HTML in markdown through verbatim, and entry bodies are
 * written by other users (and by agents ingesting untrusted web content), so
 * rendered markdown must be sanitized before it reaches the DOM.
 */
import DOMPurify from 'dompurify';

/** Sanitize rendered markdown. Keeps ids, classes and data-* attributes, which
 * heading anchors, block-id anchors, wikilinks and callouts rely on. */
export function sanitizeHtml(html: string): string {
	return DOMPurify.sanitize(html, {
		USE_PROFILES: { html: true },
		FORBID_TAGS: ['style', 'form', 'input', 'button', 'textarea', 'select'],
		FORBID_ATTR: ['style']
	});
}

/** Serialize data for embedding inside a <script> element. JSON.stringify
 * leaves "</script>" intact, which would end the element early and let the
 * rest of the string run as markup. Escaping "<" keeps the JSON equivalent. */
export function jsonForScriptTag(data: unknown): string {
	return JSON.stringify(data).replace(/</g, '\\u003c');
}
