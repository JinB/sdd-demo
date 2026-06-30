<?php
/**
 * Plugin Name: SDD Deploy Trigger
 * Description: Triggers GitHub Actions rebuild when a post is published or updated.
 */

define('SDD_GH_TOKEN', getenv('GH_DEPLOY_TOKEN') ?: '');
define('SDD_GH_REPO',  'JinB/sdd-demo');

add_action('save_post', function ($post_id) {
    if (wp_is_post_revision($post_id) || wp_is_post_autosave($post_id)) return;
    if (get_post_status($post_id) !== 'publish') return;

    $token = SDD_GH_TOKEN;
    error_log("[SDD] save_post fired for post $post_id. Token set: " . ($token ? 'YES' : 'NO'));

    $response = wp_remote_post('https://api.github.com/repos/' . SDD_GH_REPO . '/dispatches', [
        'headers' => [
            'Accept'        => 'application/vnd.github+json',
            'Authorization' => 'Bearer ' . $token,
            'User-Agent'    => 'WordPress/SDD',
        ],
        'body'    => json_encode(['event_type' => 'wordpress-post-change']),
        'timeout' => 10,
    ]);

    if (is_wp_error($response)) {
        error_log('[SDD] GitHub API error: ' . $response->get_error_message());
    } else {
        $code = wp_remote_retrieve_response_code($response);
        $body = wp_remote_retrieve_body($response);
        error_log("[SDD] GitHub API response: HTTP $code — $body");
    }
});
