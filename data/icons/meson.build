icon_themes = ['hicolor']
foreach theme : icon_themes
  scalable_dir = join_paths(theme, 'scalable/apps/')
  scalable_icon = join_paths(scalable_dir, meson.project_name() + '.svg')
  dest_scalable = join_paths(get_option('prefix'), 'share/icons', scalable_dir)
  install_data(scalable_icon,
              install_dir: dest_scalable,
              rename: '@0@.svg'.format(application_id))

endforeach

