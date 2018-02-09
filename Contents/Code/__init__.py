import urllib, urllib2, os, re, json
from datetime import datetime

PlexPorn_API = "http://theporndb.herokuapp.com/api/scenes/"
def PlexPorn_query(query):
  req = urllib2.Request(PlexPorn_API,
        json.dumps({'query':query}), {'Content-Type': 'application/json'}
      )
  response = urllib2.urlopen(req)
  return json.loads( response.read() )

class PlexPorn(Agent.Movies):

  name = "Plex Porn Media Agent"
  languages = [Locale.Language.English]
  primary_provider = False

  def search( self, results, media, lang, manual):
    filename = media.items[0].parts[0].file
    folder = os.path.basename( os.path.dirname( filename ) ).lower().strip()
    filename = os.path.basename( filename )
    unique_id = None

    # try and extract a unique id
    m = re.search( r"\{(\S+)\}\.\w+$", filename )
    if m:
      unique_id = m.groups()[0]
    
      # check to see if in database
      for scene in PlexPorn_query({'unique_id': unique_id}):
        results.Append(MetadataSearchResult(id=unique_id,score=100,name=scene['title']))
        return

    
    # match using date site combo 
    # from database
    m_date = re.search( r"\((\d{4}\-\d{2}\-\d{2})\)", filename )
    if not m_date:
      return
    
    for scene in PlexPorn_query({'date':m_date.groups()[0],'site':folder}):
      results.Append(MetadataSearchResult(id=scene['unique_id'],score=100,name=scene['title']))
      return

    # grab matching title
    m_title = re.search( r"^([^\[]+)\s{,}\[", filename )
    if not m_title:
      return
    Log( m_title.groups()[0] )

    # grab actors
    actors = ""
    m_actors = re.search( r"\[([^\]]+)\]", filename )
    if m_actors:
      actors = m_actors.groups()[0]
    
    unique_id = "|".join([ m_title.groups()[0], actors, m_date.groups()[0],folder ])
    results.Append(MetadataSearchResult(id=unique_id,score=100,name=m_title.groups()[0]))
    
  def update( self, metadata, media, lang, force):
    scene = None

    # check if we have a unique_id
    if "|" not in metadata.id:
      for scene in PlexPorn_query({'unique_id':metadata.id}):
        scene=scene
        break    
    else:
      (title,actors,date,site) = metadata.id.split("|")
      scene['title']=title; scene['actors'] = actors.split(","); scene['date'] = date
      scene['site'] = site
    if not scene:
      return

    # update scene
    if scene['title']:
      metadata.title = scene['title']
    if scene['site']:
      metadata.collections = [ scene['site'] ]
    if scene['description']:
      metadata.summary = scene['description']
    if scene['paysite']:
      metadata.studio = scene['paysite']
    if scene['date']:
      date = datetime.strptime( scene['date'], '%Y-%m-%d' )
      metadata.year = int( scene['date'].split("-")[0] ) 
      metadata.originally_available_at = date.date()
    
    # grab actors
    if 'actors' in scene:
      if len( scene['actors'] ) > 0 :
        metadata.roles.clear()

        for actor in scene['actors']:
          role = metadata.roles.new()
          role.name = actor
