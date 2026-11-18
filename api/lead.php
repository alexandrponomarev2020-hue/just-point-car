<?php
declare(strict_types=1);
ini_set('display_errors', '0');
ini_set('log_errors', '1');
date_default_timezone_set('Europe/Moscow');

header('Content-Type: application/json; charset=UTF-8');
header('Cache-Control: no-store, max-age=0');
header('X-Content-Type-Options: nosniff');

function respond(int $status, array $payload): void
{
    http_response_code($status);
    echo json_encode($payload, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
}

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    header('Allow: POST');
    http_response_code(405);
    respond(405, ['ok' => false, 'error' => 'method_not_allowed']);
}

$contentLength = (int) ($_SERVER['CONTENT_LENGTH'] ?? 0);
if ($contentLength > 20000) {
    respond(413, ['ok' => false, 'error' => 'request_too_large']);
}

$host = strtolower((string) ($_SERVER['HTTP_HOST'] ?? ''));
$origin = (string) ($_SERVER['HTTP_ORIGIN'] ?? '');
if ($origin !== '' && $host !== '') {
    $originHost = strtolower((string) parse_url($origin, PHP_URL_HOST));
    $hostWithoutPort = preg_replace('/:\\d+$/', '', $host);
    if ($originHost !== $hostWithoutPort) {
        respond(403, ['ok' => false, 'error' => 'origin_not_allowed']);
    }
}

function clean_text($value, int $limit): string
{
    if (!is_string($value)) {
        respond(422, ['ok' => false, 'error' => 'validation_failed']);
    }
    $value = trim((string) $value);
    $value = preg_replace('/[\\x00-\\x08\\x0B\\x0C\\x0E-\\x1F\\x7F]/u', '', $value) ?? '';
    if (function_exists('mb_substr')) {
        return mb_substr($value, 0, $limit, 'UTF-8');
    }
    return substr($value, 0, $limit);
}

if (clean_text($_POST['website'] ?? '', 200) !== '') {
    respond(200, ['ok' => true]);
}

$name = clean_text($_POST['name'] ?? '', 80);
$phone = clean_text($_POST['phone'] ?? '', 30);
$car = clean_text($_POST['car'] ?? '', 120);
$service = clean_text($_POST['service'] ?? '', 160);
$message = clean_text($_POST['message'] ?? '', 1000);
$source = clean_text($_POST['source'] ?? 'Сайт', 80);
$agree = clean_text($_POST['agree'] ?? '', 5);
$phoneDigits = preg_replace('/\\D+/', '', $phone) ?? '';

if ($name === '' || $car === '' || strlen($phoneDigits) < 10 || strlen($phoneDigits) > 15 || $agree !== '1') {
    respond(422, ['ok' => false, 'error' => 'validation_failed']);
}

$ip = (string) ($_SERVER['REMOTE_ADDR'] ?? 'unknown');
$rateFile = sys_get_temp_dir() . '/jpc-lead-' . hash('sha256', $ip);
if (is_file($rateFile) && (time() - (int) filemtime($rateFile)) < 20) {
    respond(429, ['ok' => false, 'error' => 'rate_limited']);
}
@touch($rateFile);

$config = [];
$secretFile = dirname(__DIR__, 2) . '/jpc-secrets.php';
if (is_file($secretFile)) {
    $loadedConfig = require $secretFile;
    if (is_array($loadedConfig)) {
        $config = $loadedConfig;
    }
}

$token = (string) (getenv('JPC_TELEGRAM_BOT_TOKEN') ?: ($config['bot_token'] ?? ''));
$chatIdsValue = getenv('JPC_TELEGRAM_CHAT_IDS');
$chatIdsValue = $chatIdsValue !== false ? $chatIdsValue : ($config['chat_ids'] ?? []);
$chat_ids = is_array($chatIdsValue) ? $chatIdsValue : explode(',', (string) $chatIdsValue);
$chat_ids = array_values(array_unique(array_filter(array_map('trim', $chat_ids), static function ($id): bool {
    return $id !== '';
})));

if (!preg_match('/^\\d+:[A-Za-z0-9_-]{20,}$/', $token) || count($chat_ids) !== 1) {
    error_log('JPC lead handler is not configured');
    respond(503, ['ok' => false, 'error' => 'service_not_configured']);
}

function html(string $value): string
{
    return htmlspecialchars($value, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

$lines = [
    '<b>Новая заявка с сайта Just Point Car</b>',
    '',
    '<b>Имя:</b> ' . html($name),
    '<b>Телефон:</b> ' . html($phone),
    '<b>Автомобиль:</b> ' . html($car),
];
if ($service !== '') {
    $lines[] = '<b>Услуга:</b> ' . html($service);
}
if ($message !== '') {
    $lines[] = '<b>Задача:</b> ' . html($message);
}
$lines[] = '';
$lines[] = '<b>Форма:</b> ' . html($source);
$lines[] = '<b>Время:</b> ' . date('d.m.Y H:i');
$telegramText = implode("\n", $lines);

function telegram_send(string $url, array $payload): bool
{
    $body = http_build_query($payload, '', '&', PHP_QUERY_RFC3986);

    if (function_exists('curl_init')) {
        $curl = curl_init($url);
        curl_setopt_array($curl, [
            CURLOPT_POST => true,
            CURLOPT_POSTFIELDS => $body,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_CONNECTTIMEOUT => 5,
            CURLOPT_TIMEOUT => 10,
            CURLOPT_HTTPHEADER => ['Content-Type: application/x-www-form-urlencoded'],
        ]);
        $response = curl_exec($curl);
        $status = (int) curl_getinfo($curl, CURLINFO_HTTP_CODE);
        unset($curl);
    } else {
        $context = stream_context_create(['http' => [
            'method' => 'POST',
            'header' => "Content-Type: application/x-www-form-urlencoded\r\n",
            'content' => $body,
            'timeout' => 10,
            'ignore_errors' => true,
        ]]);
        $response = @file_get_contents($url, false, $context);
        $status = 200;
    }

    if (!is_string($response) || $status < 200 || $status >= 300) {
        return false;
    }
    $decoded = json_decode($response, true);
    return is_array($decoded) && ($decoded['ok'] ?? false) === true;
}

$apiBase = rtrim((string) (getenv('JPC_TELEGRAM_API_BASE') ?: 'https://api.telegram.org'), '/');
$telegramUrl = $apiBase . '/bot' . $token . '/sendMessage';
$allSent = true;
foreach ($chat_ids as $index => $chatId) {
    $sent = telegram_send($telegramUrl, [
        'chat_id' => $chatId,
        'text' => $telegramText,
        'parse_mode' => 'HTML',
        'disable_web_page_preview' => 'true',
    ]);
    if (!$sent) {
        $allSent = false;
        error_log('JPC Telegram delivery failed for recipient ' . (string) $index);
    }
}

if (!$allSent) {
    respond(502, ['ok' => false, 'error' => 'delivery_failed']);
}

respond(200, ['ok' => true]);
