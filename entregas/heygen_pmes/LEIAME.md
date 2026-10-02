# PMES com o avatar "Terno Bege" (HeyGen)

Pedido do Dr. Casil (02/10/2026): refazer a gravação do PMES Soldado 2026 feita no teleprompter
(arquivo 84 do Redes, 43 s, câmera deitada e áudio com o tratamento de chamada do navegador)
com o avatar **Terno Bege** do HeyGen, mantendo a fala e a voz dele.

`pmes_voz_editada.mp3` (29,8 s) é o áudio original, tratado:
- declip, passa-alta de 80 Hz, redução de ruído leve, compressão suave e loudnorm de -16 LUFS;
- cortados o silêncio do começo e as pausas longas (4,8 s e 3,9 s);
- cortado o trecho "e o prazo de recurso já está correndo": o prazo já tinha acabado.

Sobrou na fala "10 questões passíveis de recurso" (não dá para trocar sem sintetizar a voz).

## Geração (precisa de HEYGEN_API_KEY no ambiente)

1. Subir o áudio: `POST https://upload.heygen.com/v1/asset` com `Content-Type: audio/mpeg`, o corpo
   sendo o MP3 e o header `X-Api-Key`. Guardar o id do asset.
2. Achar o avatar cujo nome contém "Terno Bege" (`/v2/avatars` e `/v2/avatar_group.list`).
3. `POST https://api.heygen.com/v2/video/generate`: `dimension` 1080x1920; em `video_inputs`,
   `character` com o avatar e `voice` como `{"type": "audio", "audio_asset_id": "<id>"}`.
4. Acompanhar com `/v1/video_status.get`, baixar o MP4 e conferir a sincronia da boca.
5. Opcional: passar o resultado pela skill reel-silvapinto (legenda, infográficos e encerramento).
