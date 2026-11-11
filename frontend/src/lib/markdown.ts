import { Marked, type Renderer, type Tokens } from 'marked';

const escapeHtml = (value: string) =>
	value
		.replace(/&/g, '&amp;')
		.replace(/</g, '&lt;')
		.replace(/>/g, '&gt;')
		.replace(/"/g, '&quot;')
		.replace(/'/g, '&#39;');

// Solo enlaces web, correo, internos (/ruta) y anclas.
const SAFE_HREF = /^(https?:\/\/|mailto:|\/(?!\/)|#)/i;

const markdown = new Marked({
	async: false,
	gfm: true,
	renderer: {
		// El HTML crudo se muestra como texto: el contenido puede venir de propuestas de usuarios.
		html: ({ text }: Tokens.HTML | Tokens.Tag) => escapeHtml(text),
		image: ({ text }: Tokens.Image) => escapeHtml(text),
		link(this: Renderer, { href, title, tokens }: Tokens.Link) {
			const label = this.parser.parseInline(tokens);
			if (!SAFE_HREF.test(href)) return label;
			const titleAttr = title ? ` title="${escapeHtml(title)}"` : '';
			return `<a href="${escapeHtml(href)}"${titleAttr}>${label}</a>`;
		}
	}
});

/** Markdown -> HTML seguro para insertar con {@html}. */
export function renderMarkdown(source: string): string {
	return markdown.parse(source) as string;
}
