# Sistema de Idioma Universal e Traduções — Pixelia Livre

O **Pixelia Livre** detecta automaticamente o idioma de exibição do **Windows** ao iniciar e traduz **toda a interface, habilidades, atributos, status e mensagens de erro** (incluindo retornos de `backend.py`, `bootstrap.py`, `agent.js`, `basketball.js` e `minigames.js`).

---

## 1. Como funciona a detecção automática do Windows

No arquivo [`src/i18n.py`](../src/i18n.py), a função `detect_windows_tags()` consulta as APIs nativas do Windows na seguinte ordem de prioridade:

1. `kernel32.GetUserPreferredUILanguages(0x8)` — lista ordenada de idiomas de exibição preferidos do usuário no Windows (tags BCP-47, como `pt-BR`, `en-US`, `es-419`, `zh-TW`).
2. `kernel32.GetUserDefaultUILanguage()` — idioma padrão da interface do usuário no Windows (`LANGID` convertido via `locale.windows_locale`).
3. `kernel32.GetSystemDefaultUILanguage()` — idioma padrão do sistema.
4. `locale.getlocale()` — fallback padrão do Python.

O sistema compara os códigos encontrados com os pacotes disponíveis:
- Se encontrar correspondência exata ou por subtag base (ex.: `pt-BR` → `pt`, `es-MX` → `es`, `zh-CN` → `zh-Hans`, `zh-TW` → `zh-Hant`), o painel já abre nesse idioma.
- Se o Windows estiver em um idioma que ainda não possui pacote nativo, o painel usa **Inglês (`en`)** como fallback universal.
- Você também pode trocar o idioma manualmente a qualquer momento pelo seletor no canto superior direito do painel (mantendo a conexão com o jogo e a habilidade selecionada).

---

## 2. Idiomas já incluídos nativamente (13 idiomas)

| Código | Idioma | Arquivo |
| --- | --- | --- |
| `pt` | Português | [`src/locales/pt.json`](../src/locales/pt.json) |
| `en` | English *(fallback universal)* | [`src/locales/en.json`](../src/locales/en.json) |
| `es` | Español | [`src/locales/es.json`](../src/locales/es.json) |
| `fr` | Français | [`src/locales/fr.json`](../src/locales/fr.json) |
| `de` | Deutsch | [`src/locales/de.json`](../src/locales/de.json) |
| `it` | Italiano | [`src/locales/it.json`](../src/locales/it.json) |
| `pl` | Polski | [`src/locales/pl.json`](../src/locales/pl.json) |
| `ru` | Русский | [`src/locales/ru.json`](../src/locales/ru.json) |
| `tr` | Türkçe | [`src/locales/tr.json`](../src/locales/tr.json) |
| `ja` | 日本語 | [`src/locales/ja.json`](../src/locales/ja.json) |
| `ko` | 한국어 | [`src/locales/ko.json`](../src/locales/ko.json) |
| `zh-Hans` | 简体中文 (Chinês Simplificado) | [`src/locales/zh-Hans.json`](../src/locales/zh-Hans.json) |
| `zh-Hant` | 繁體中文 (Chinês Tradicional) | [`src/locales/zh-Hant.json`](../src/locales/zh-Hant.json) |

---

## 3. Como traduzir o mod para QUALQUER outro idioma (sem recompilar)

Você pode adicionar novos idiomas ou personalizar textos existentes sem precisar de Python ou recompilar o `.exe`:

1. Abra a pasta `locales\` ao lado do `PixeliaLivre.exe` (ou [`src/locales/`](../src/locales) no código-fonte) e copie o arquivo `_template.json`.
2. Renomeie a cópia para o código BCP-47 do idioma desejado (exemplos: `nl.json` para Holandês, `uk.json` para Ucraniano, `ar.json` para Árabe, `vi.json` para Vietnamita).
3. Edite o bloco `meta` no topo do JSON:
   ```json
   "meta": {
     "code": "nl",
     "name": "Dutch",
     "native_name": "Nederlands",
     "match_tags": ["nl", "nl-nl", "nl-be"]
   }
   ```
4. Ajuste `number_format` (`thousands` e `decimal`), traduza `skills`, `patterns` (mantendo os marcadores como `{value}`, `{min}`, `{max}`, `{name}`, `{build}`, `{details}`) e os textos em `strings`.
   - *Dica:* qualquer chave que você deixar sem traduzir em um arquivo externo cai automaticamente no fallback universal em Inglês (`en.json`) — o painel nunca quebra.
5. Reinicie o `PixeliaLivre.exe`: o idioma aparecerá automaticamente no seletor do painel e será selecionado sozinho caso o seu Windows esteja nesse idioma (`match_tags`).

Se quiser compartilhar sua tradução com a comunidade, envie um Pull Request adicionando o JSON em `src/locales/`!
