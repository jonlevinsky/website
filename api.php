<?php
header('Content-Type: application/json; charset=utf-8');

$action = $_GET['action'] ?? '';

if ($action === 'save_json') {
    $data = file_get_contents('php://input');
    $decoded = json_decode($data);
    if (json_last_error() === JSON_ERROR_NONE) {
        if (file_put_contents('projects.json', $data)) {
            echo json_encode(['success' => true]);
        } else {
            echo json_encode(['success' => false, 'error' => 'Nelze zapsat do souboru projects.json']);
        }
    } else {
        echo json_encode(['success' => false, 'error' => 'Neplatný JSON formát']);
    }
    exit;
}

if ($action === 'upload') {
    $basePath = $_POST['base'] ?? 'photo'; // 'photo' or 'video'
    $folder = $_POST['folder'] ?? 'Bez Názvu';
    
    // Sanitize values
    $basePath = basename(str_replace(['\\', '/'], '', $basePath));
    $folder = str_replace(['..', '\\', '/'], '', $folder);
    
    if (!$basePath || !in_array($basePath, ['photo', 'video'])) {
        $basePath = 'photo';
    }
    
    $dir = __DIR__ . '/' . $basePath . '/' . $folder;
    
    if (!is_dir($dir)) {
        if (!mkdir($dir, 0777, true)) {
            echo json_encode(['success' => false, 'error' => 'Nelze vytvořit složku ' . $dir]);
            exit;
        }
    }
    
    $uploadedFiles = [];
    $errors = [];
    
    if (isset($_FILES['files'])) {
        $files = $_FILES['files'];
        // Společný formátování pro jeden i více souborů
        if (!is_array($files['name'])) {
            $files = [
                'name' => [$files['name']],
                'type' => [$files['type']],
                'tmp_name' => [$files['tmp_name']],
                'error' => [$files['error']],
                'size' => [$files['size']]
            ];
        }

        for ($i = 0; $i < count($files['name']); $i++) {
            if ($files['error'][$i] === UPLOAD_ERR_OK) {
                $filename = basename($files['name'][$i]);
                $target = $dir . '/' . $filename;
                
                if (move_uploaded_file($files['tmp_name'][$i], $target)) {
                    $uploadedFiles[] = [
                        'name' => $filename,
                        'path' => './' . $basePath . '/' . $folder . '/' . $filename
                    ];
                } else {
                    $errors[] = "Chyba při přesunu souboru " . $filename;
                }
            } else {
                if ($files['error'][$i] !== UPLOAD_ERR_NO_FILE) {
                    $errors[] = "Chyba uploadu (kód: " . $files['error'][$i] . ")";
                }
            }
        }
    }
    
    echo json_encode([
        'success' => true, 
        'uploaded' => $uploadedFiles, 
        'errors' => $errors
    ]);
    exit;
}

echo json_encode(['success' => false, 'error' => 'Neznámá akce']);
?>
