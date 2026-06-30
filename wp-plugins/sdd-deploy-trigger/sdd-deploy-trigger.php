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

    wp_remote_post('https://api.github.com/repos/' . SDD_GH_REPO . '/dispatches', [
        'headers' => [
            'Accept'        => 'application/vnd.github+json',
            'Authorization' => 'Bearer ' . SDD_GH_TOKEN,
            'User-Agent'    => 'WordPress/SDD',
        ],
        'body'    => json_encode(['event_type' => 'wordpress-post-change']),
        'timeout' => 10,
    ]);
});
