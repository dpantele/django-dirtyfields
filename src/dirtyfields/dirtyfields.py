# Adapted from http://stackoverflow.com/questions/110803/dirty-fields-in-django
from django.db.models.signals import post_save
import django

class DirtyFieldsMixin(object):
    def __init__(self, *args, **kwargs):
        super(DirtyFieldsMixin, self).__init__(*args, **kwargs)
        post_save.connect(reset_state, sender=self.__class__,
                            dispatch_uid='%s-DirtyFieldsMixin-sweeper' % self.__class__.__name__)
        reset_state(sender=self.__class__, instance=self)

    def _as_dict(self):
        return dict((f.name, f.to_python(getattr(self, f.attname))) for f in self._meta.local_fields)

    def get_dirty_fields(self):
        """
        Returns a list of keys that have changed
        """
        new_state = self._as_dict()
        return tuple(k for k, v in self._original_state.iteritems() if v != new_state[k])

    @property
    def is_dirty(self):
        # in order to be dirty we need to have been saved at least once, so we
        # check for a primary key and we need our dirty fields to not be empty
        if self._state.adding:
            return True
        return bool(self.get_dirty_fields())

    def save(self, *args, **kwargs):
        if django.VERSION >= (1,5,0):
            kwargs['update_fields'] = self.get_dirty_fields()
        
        return super(DirtyFieldsMixin, self).save(*args, **kwargs)


def reset_state(sender, instance, **kwargs):
    instance._original_state = instance._as_dict()
