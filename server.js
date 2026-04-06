const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 3000;

const mimeTypes = {
  '.html': 'text/html',
  '.js': 'text/javascript',
  '.css': 'text/css',
  '.json': 'application/json',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif': 'image/gif',
  '.svg': 'image/svg+xml',
  '.wav': 'audio/wav',
  '.mp4': 'video/mp4',
  '.webm': 'video/webm',
  '.woff': 'application/font-woff',
  '.ttf': 'application/font-ttf',
  '.eot': 'application/vnd.ms-fontobject',
  '.otf': 'application/font-otf',
  '.wasm': 'application/wasm'
};

const server = http.createServer((req, res) => {
  console.log(`${req.method} ${req.url}`);

  // Simulace api.php přes Node.js server (pro plnou kompatibilitu lokálně)
  if (req.method === 'POST' && req.url.includes('api.php?action=')) {
    let chunks = [];
    req.on('data', chunk => chunks.push(chunk));
    req.on('end', () => {
      try {
        const body = Buffer.concat(chunks).toString('utf8');
        const data = JSON.parse(body);

        if (req.url.includes('action=save_json')) {
          fs.writeFileSync(path.join(__dirname, 'projects.json'), JSON.stringify(data, null, 2));
          console.log(`✅ Data z builderu uložena do projects.json!`);
          res.writeHead(200, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ success: true }));
          return;
        }

        if (req.url.includes('action=upload')) {
          const basePath = data.base || 'photo';
          const folder = data.folder || 'Bez Názvu';
          const targetDir = path.join(__dirname, basePath, folder);

          // Zabezpeč vytvoření složky, pokud neexistuje
          if (!fs.existsSync(targetDir)) {
            fs.mkdirSync(targetDir, { recursive: true });
          }

          const uploaded = [];
          const errors = [];

          if (data.files && Array.isArray(data.files)) {
            for (const file of data.files) {
              try {
                // Odříznutí identifikátoru base64 hlavičky "data:image/png;base64,"
                const base64Data = file.data.replace(/^data:([A-Za-z-+/]+);base64,/, '');
                const filePath = path.join(targetDir, file.name);
                
                fs.writeFileSync(filePath, base64Data, 'base64');
                uploaded.push({ name: file.name, path: `./${basePath}/${folder}/${file.name}` });
                console.log(`✅ Podařilo se nahrát úpěšně soubor z builderu: ${file.name}`);
              } catch (e) {
                console.error(`❌ Nelze uložit soubor: ${file.name}`, e);
                errors.push(`Chyba při ukládání souboru ${file.name}`);
              }
            }
          }

          res.writeHead(200, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ success: true, uploaded, errors }));
          return;
        }

      } catch (e) {
        console.error('❌ Server API error:', e.message);
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: false, error: e.message }));
      }
    });
    return;
  }

  // Statický HTTP server
  let rawUrl = req.url.split('?')[0];
  let requestUrl = decodeURIComponent(rawUrl);
  let filePath = '.' + requestUrl;
  if (filePath === './') {
    filePath = './index.html';
  }

  const absPath = path.join(__dirname, filePath.substring(1));
  const extname = String(path.extname(absPath)).toLowerCase();
  const contentType = mimeTypes[extname] || 'application/octet-stream';

  fs.stat(absPath, (err, stats) => {
    if (err) {
      if (err.code === 'ENOENT') {
        res.writeHead(404, { 'Content-Type': 'text/plain' });
        res.end('404 Not Found: ' + absPath);
      } else {
        res.writeHead(500, { 'Content-Type': 'text/plain' });
        res.end('500 Internal Error: ' + err.code);
      }
      return;
    }

    // Podpora pro streamování videa (Range requesty)
    if (req.headers.range) {
      const range = req.headers.range;
      const parts = range.replace(/bytes=/, "").split("-");
      const partialstart = parts[0];
      const partialend = parts[1];

      let start = parseInt(partialstart, 10);
      let end = partialend ? parseInt(partialend, 10) : stats.size - 1;

      // Očištění a ožetření chyb zakreslení
      if (isNaN(start)) {
        start = stats.size - end;
        end = stats.size - 1;
      }
      if (isNaN(end)) {
        end = stats.size - 1;
      }
      
      if (start >= stats.size) {
        res.writeHead(416, { 'Content-Range': `bytes */${stats.size}` });
        return res.end();
      }

      const chunksize = (end - start) + 1;

      res.writeHead(206, {
        'Content-Range': `bytes ${start}-${end}/${stats.size}`,
        'Accept-Ranges': 'bytes',
        'Content-Length': chunksize,
        'Content-Type': contentType,
      });

      const stream = fs.createReadStream(absPath, { start, end });
      stream.on('error', err => {
        if (!res.headersSent) {
          res.writeHead(500);
          res.end('File stream error');
        }
      });
      stream.pipe(res);
    } else {
      res.writeHead(200, {
        'Content-Length': stats.size,
        'Content-Type': contentType,
      });
      fs.createReadStream(absPath).pipe(res);
    }
  });
});

server.listen(PORT, () => {
  console.log(`\n🚀 Lokální server pro portfolio běží na adrese: http://localhost:${PORT}`);
  console.log('Tento server plně simuluje Node.js chování PHP (pro upload souborů a ukládání JSON).');
  console.log('Zastavíte jej stisknutím kláves CMD+C nebo CTRL+C v terminálu.\n');
});
