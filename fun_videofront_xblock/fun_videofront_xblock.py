import logging
import pkg_resources

from django.utils.translation import ugettext_lazy
from django.template import Context, Template

from xblock.core import XBlock
from xblock.fields import Boolean, Scope, String
from xblock.fragment import Fragment
from xblockutils.studio_editable import StudioEditableXBlockMixin

# Note that the videofront SDK from FUN is required to use this XBlock.
from videoproviders.api import videofront


logger = logging.getLogger(__name__)


@XBlock.needs('settings')
class FunVideofrontXBlock(StudioEditableXBlockMixin, XBlock):
    """
    Play videos based on a modified videojs player. This XBlock supports
    subtitles and multiple resolutions.
    """

    display_name = String(
        help=ugettext_lazy("The name students see. This name appears in "
                           "the course ribbon and as a header for the video."),
        display_name=ugettext_lazy("Component Display Name"),
        default=ugettext_lazy("New video"),
        scope=Scope.settings
    )

    video_id = String(
        scope=Scope.settings,
        help=ugettext_lazy('Fill this with the ID of the video found in the video uploads dashboard'),
        default="",
        display_name=ugettext_lazy('Video ID')
    )

    allow_download = Boolean(
        help=ugettext_lazy("Allow students to download this video."),
        display_name=ugettext_lazy("Video download allowed"),
        scope=Scope.settings,
        default=True
    )

    editable_fields = ('display_name', 'video_id', 'allow_download', )


    @property
    def course_key_string(self):
        return unicode(self.location.course_key)

    @property
    def video_id_clean(self):
        return None if self.video_id is None else self.video_id.strip()

    def get_icon_class(self):
        """CSS class to be used in courseware sequence list."""
        return 'video'

    def student_view(self, context=None):
        fragment = Fragment()
        template_content = self.resource_string("public/html/xblock.html")
        template = Template(template_content)
        messages = []# tuple list
        context = {
            'display_name': self.display_name,
            'video_id': self.video_id_clean,
            'messages': messages,
            'video': {},
            'allow_download': self.allow_download,
            'downloads': [],
        }
        if self.video_id_clean:
            try:
                videofront_client = videofront.Client(self.course_key_string)
                video = videofront_client.get_video_with_subtitles(self.video_id_clean)
                context['video'] = video
                download_labels = {
                    'HD': 'Haute (1080p)',
                    'SD': 'Normale (720p)',
                    'LD': 'Mobile (480p)',
                }

                # Sort download links by decreasing bitrates
                video_sources = video['video_sources'][::-1]
                context['downloads'] = [
                    {
                        'url': source['url'],
                        'label': download_labels.get(source['label'], source['label'])
                    }
                    for source in video_sources
                ]

            except videofront.MissingCredentials as e:
                messages.append(('error', e.verbose_message))
            except videofront.ClientError as e:
                # Note that we may not log an exception here, because unicode
                # messages cannot be encoded by the logger
                logger.error(e.message)
                messages.append(('error', ugettext_lazy("An unexpected error occurred.")))
        else:
            messages.append(('warning', ugettext_lazy(
                "You need to define a valid video ID. "
                "Video IDs for your course can be found in the video upload"
                " dashboard."
            )))

        content = template.render(Context(context))
        fragment.add_content(content)

        fragment.add_css(self.resource_string("public/css/xblock.css"))
        # This hack requires us to hardcode the url to the css file.
        # see no other way to proceed.  Loading static files directly from
        # fun-apps/edx-platform is unconventional. It would be great to find a
        # workaround.
        fragment.add_css_url("/static/fun/js/vendor/videojs/video-js.min.css")
        fragment.add_javascript(self.resource_string("public/js/xblock.js"))

        fragment.initialize_js("FunVideofrontXBlock", json_args={
            'course_id': self.course_key_string,
            'video_id': self.video_id_clean,
        })

        return fragment

    def resource_string(self, path):
        """Handy helper for getting resources from our kit."""
        data = pkg_resources.resource_string(__name__, path)
        return data.decode("utf8")
