<?php
// save_reviews.php
// Povolit přístup pouze pro POST požadavky
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['success' => false, 'error' => 'Method Not Allowed']);
    exit;
}

// Získat JSON data z těla požadavku
$data = file_get_contents('php://input');

// Ověřit, že jde o validní JSON
$decoded = json_decode($data);
if (json_last_error() !== JSON_ERROR_NONE) {
    http_response_code(400);
    echo json_encode(['success' => false, 'error' => 'Invalid JSON']);
    exit;
}

// Cesta k souboru (ujistěte se, že složka data/ má práva pro zápis - chmod 777 nebo 775)
$file_path = __DIR__ . '/data/reviews.json';

// Uložit do souboru
if (file_put_contents($file_path, $data)) {
    echo json_encode(['success' => true]);
} else {
    http_response_code(500);
    echo json_encode(['success' => false, 'error' => 'Could not save file. Check directory permissions.']);
}
?>
